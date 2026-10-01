//! Reading interpretation with the Claude API, called straight from Rust over HTTPS (Rust has no official SDK).
//!
//! The key is read from the OS credential store here and never reaches the frontend. The system prompt is
//! compiled in from src/data/interpret-system.md (the frontend shows the same file for "copy the prompt"),
//! so the page can only supply the reading itself. The answer is streamed to the page through a Channel.

use crate::{api_key, config};
use futures_util::StreamExt;
use serde::Serialize;
use serde_json::{json, Value};
use std::collections::HashSet;
use std::sync::Mutex;
use std::time::Duration;
use tauri::ipc::Channel;

const API_URL: &str = "https://api.anthropic.com/v1/messages";
const API_VERSION: &str = "2023-06-01";
/// Server-side fallback ("fallbacks": "default"): a request declined by the safety classifiers is retried on
/// Anthropic's recommended model for that refusal category, on the same stream.
/// https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback
const FALLBACK_BETA: &str = "server-side-fallback-2026-07-01";
const MAX_TOKENS: u32 = 16000;

pub const SYSTEM_PROMPT: &str = include_str!("../../src/data/interpret-system.md");

/// Requests the page asked to stop (it left the screen or pressed stop).
#[derive(Default)]
pub struct Cancels(pub Mutex<HashSet<String>>);

#[derive(Clone, Serialize)]
#[serde(tag = "type", rename_all = "camelCase")]
pub enum StreamEvent {
    /// The stream opened; `model` is the model that is answering.
    Start { model: String },
    Text { text: String },
    /// The requested model declined and `to` continues the answer.
    Fallback { to: String },
}

#[derive(Default, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Summary {
    pub model: String,
    pub stop_reason: Option<String>,
    pub input_tokens: u64,
    pub output_tokens: u64,
    pub cache_read_tokens: u64,
    pub cache_write_tokens: u64,
    pub cancelled: bool,
}

/// Public settings for the page: never the key itself.
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct AiConfig {
    pub model: String,
    pub has_key: bool,
    pub key_last4: Option<String>,
}

pub fn ai_config() -> Result<AiConfig, String> {
    let has_key = api_key::get_api_key()?.is_some();
    let key_last4 = config::load()?
        .get(config::KEY_LAST4)
        .and_then(|v| v.as_str())
        .map(str::to_string)
        .filter(|_| has_key);
    Ok(AiConfig { model: config::model(), has_key, key_last4 })
}

fn request_body(model: &str, prompt: &str) -> Value {
    json!({
        "model": model,
        "max_tokens": MAX_TOKENS,
        "stream": true,
        // The system prompt is the same on every call, so it is cached (5 minutes); the reading is not.
        "system": [{ "type": "text", "text": SYSTEM_PROMPT, "cache_control": { "type": "ephemeral" } }],
        "messages": [{ "role": "user", "content": prompt }],
        "output_config": { "effort": "medium" },
        "fallbacks": "default",
    })
}

/// A short Japanese message for the page, from the HTTP status and the API's error body.
fn http_error(status: u16, body: &str) -> String {
    let detail = serde_json::from_str::<Value>(body)
        .ok()
        .and_then(|v| v["error"]["message"].as_str().map(str::to_string))
        .unwrap_or_default();
    let head = match status {
        400 => "リクエストの内容に問題がありました",
        401 => "APIキーが正しくないか、無効になっています。設定でキーを確認してください",
        403 => "このAPIキーでは利用できません（権限または利用地域）",
        404 => "モデルが見つかりません。設定のモデル名を確認してください",
        413 => "リクエストが大きすぎます",
        429 => "利用の上限に達しました。しばらく待ってから再度お試しください",
        500..=599 => "APIが混み合っているか、一時的な障害です。しばらく待ってから再度お試しください",
        _ => "APIの呼び出しに失敗しました",
    };
    if detail.is_empty() { format!("{head}（HTTP {status}）") } else { format!("{head}（HTTP {status}: {detail}）") }
}

/// One server-sent event's JSON payload.
fn handle_event(data: &Value, summary: &mut Summary, on_event: &Channel<StreamEvent>) -> Result<(), String> {
    match data["type"].as_str().unwrap_or_default() {
        "message_start" => {
            let msg = &data["message"];
            summary.model = msg["model"].as_str().unwrap_or_default().to_string();
            let usage = &msg["usage"];
            summary.input_tokens = usage["input_tokens"].as_u64().unwrap_or(0);
            summary.cache_read_tokens = usage["cache_read_input_tokens"].as_u64().unwrap_or(0);
            summary.cache_write_tokens = usage["cache_creation_input_tokens"].as_u64().unwrap_or(0);
            let _ = on_event.send(StreamEvent::Start { model: summary.model.clone() });
        }
        "content_block_start" => {
            let block = &data["content_block"];
            if block["type"] == "fallback" {
                let to = block["to"]["model"].as_str().unwrap_or_default().to_string();
                summary.model = to.clone();
                let _ = on_event.send(StreamEvent::Fallback { to });
            }
        }
        "content_block_delta" => {
            // Only the answer text goes to the page (thinking blocks, if any, are skipped).
            if data["delta"]["type"] == "text_delta" {
                if let Some(text) = data["delta"]["text"].as_str() {
                    let _ = on_event.send(StreamEvent::Text { text: text.to_string() });
                }
            }
        }
        "message_delta" => {
            if let Some(reason) = data["delta"]["stop_reason"].as_str() {
                summary.stop_reason = Some(reason.to_string());
            }
            if let Some(out) = data["usage"]["output_tokens"].as_u64() {
                summary.output_tokens = out;
            }
        }
        "error" => {
            let kind = data["error"]["type"].as_str().unwrap_or_default();
            let msg = data["error"]["message"].as_str().unwrap_or_default();
            return Err(if kind == "overloaded_error" {
                "APIが混み合っています。しばらく待ってから再度お試しください".to_string()
            } else {
                format!("生成の途中でエラーが発生しました（{kind}: {msg}）")
            });
        }
        _ => {}
    }
    Ok(())
}

/// Splits complete SSE events off the front of `buf` and returns their `data:` payloads.
fn take_events(buf: &mut String) -> Vec<String> {
    let mut out = Vec::new();
    loop {
        let normalized = buf.replace("\r\n", "\n");
        let Some(end) = normalized.find("\n\n") else {
            *buf = normalized;
            break;
        };
        let event: String = normalized[..end].to_string();
        *buf = normalized[end + 2..].to_string();
        let data: Vec<&str> = event
            .lines()
            .filter_map(|l| l.strip_prefix("data:"))
            .map(|l| l.strip_prefix(' ').unwrap_or(l))
            .collect();
        if !data.is_empty() {
            out.push(data.join("\n"));
        }
    }
    out
}

pub async fn run(
    request_id: &str,
    prompt: &str,
    on_event: &Channel<StreamEvent>,
    cancels: &Cancels,
) -> Result<Summary, String> {
    let key = api_key::get_api_key()?.ok_or("APIキーが設定されていません。設定から登録してください")?;
    let model = config::model();
    let result = stream(&key, &model, request_id, prompt, on_event, cancels).await;
    cancels.0.lock().unwrap().remove(request_id);
    result.map_err(|e| api_key::redact(&e, &key))
}

async fn stream(
    key: &str,
    model: &str,
    request_id: &str,
    prompt: &str,
    on_event: &Channel<StreamEvent>,
    cancels: &Cancels,
) -> Result<Summary, String> {
    let client = reqwest::Client::builder()
        .connect_timeout(Duration::from_secs(15))
        .read_timeout(Duration::from_secs(120))
        .build()
        .map_err(|e| format!("HTTP client init failed: {e}"))?;
    let response = client
        .post(API_URL)
        .header("x-api-key", key)
        .header("anthropic-version", API_VERSION)
        .header("anthropic-beta", FALLBACK_BETA)
        .json(&request_body(model, prompt))
        .send()
        .await
        .map_err(|e| {
            if e.is_connect() || e.is_timeout() {
                "APIに接続できませんでした。インターネット接続を確認してください".to_string()
            } else {
                format!("APIの呼び出しに失敗しました（{e}）")
            }
        })?;

    let status = response.status();
    if !status.is_success() {
        let body = response.text().await.unwrap_or_default();
        return Err(http_error(status.as_u16(), &body));
    }

    let mut summary = Summary { model: model.to_string(), ..Default::default() };
    let mut bytes = response.bytes_stream();
    let mut buf = String::new();
    let mut pending: Vec<u8> = Vec::new(); // a UTF-8 character can be split across chunks
    while let Some(chunk) = bytes.next().await {
        if cancels.0.lock().unwrap().contains(request_id) {
            summary.cancelled = true;
            return Ok(summary); // dropping the response closes the connection
        }
        let chunk = chunk.map_err(|e| format!("受信中に接続が切れました（{e}）"))?;
        pending.extend_from_slice(&chunk);
        let valid = match std::str::from_utf8(&pending) {
            Ok(s) => s.len(),
            Err(e) => e.valid_up_to(),
        };
        buf.push_str(std::str::from_utf8(&pending[..valid]).unwrap_or_default());
        pending.drain(..valid);
        for data in take_events(&mut buf) {
            let Ok(value) = serde_json::from_str::<Value>(&data) else { continue };
            handle_event(&value, &mut summary, on_event)?;
        }
    }
    Ok(summary)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sse_events_are_split_and_joined() {
        let mut buf = String::from("event: message_start\ndata: {\"a\":1}\n\nevent: ping\r\ndata: {\"b\":2}\r\n\r\nevent: x\ndata: {\"c\"");
        let events = take_events(&mut buf);
        assert_eq!(events, vec!["{\"a\":1}", "{\"b\":2}"]);
        assert_eq!(buf, "event: x\ndata: {\"c\"");
    }

    #[test]
    fn request_has_cache_fallback_and_model() {
        let body = request_body("claude-sonnet-5-5", "reading");
        assert_eq!(body["model"], "claude-sonnet-5-5");
        assert_eq!(body["fallbacks"], "default");
        assert_eq!(body["system"][0]["cache_control"]["type"], "ephemeral");
        assert!(body.get("thinking").is_none());
    }

    #[test]
    fn http_errors_are_readable() {
        let msg = http_error(401, r#"{"type":"error","error":{"type":"authentication_error","message":"invalid x-api-key"}}"#);
        assert!(msg.contains("APIキー") && msg.contains("401") && msg.contains("invalid x-api-key"));
        assert!(http_error(529, "").contains("混み合って"));
    }

    fn silent_channel() -> Channel<StreamEvent> {
        Channel::new(|_| Ok(()))
    }

    /// Calls the real API with a dummy key: checks TLS, headers and the 401 message (costs nothing).
    #[tokio::test]
    #[ignore]
    async fn live_invalid_key() {
        let err = stream("sk-ant-invalid-key-for-test", config::DEFAULT_MODEL, "t", "テスト", &silent_channel(), &Cancels::default())
            .await
            .err()
            .expect("should fail");
        println!("{err}");
        assert!(err.contains("401"), "{err}");
    }

    /// Phase 5 samples: sends each <LA_SAMPLE_DIR>/*.prompt.txt (written by src/lib/samples.node.test.ts) with the
    /// key saved in the app, and writes the answer next to it. Uses the API and is billed.
    #[tokio::test]
    #[ignore]
    async fn live_samples() {
        let dir = std::path::PathBuf::from(std::env::var("LA_SAMPLE_DIR").expect("LA_SAMPLE_DIR"));
        let key = api_key::get_api_key().unwrap().expect("no API key saved in the app");
        let model = std::env::var("LA_SAMPLE_MODEL").unwrap_or_else(|_| config::model());
        let mut prompts: Vec<_> = std::fs::read_dir(&dir).unwrap().flatten().map(|e| e.path())
            .filter(|p| p.to_string_lossy().ends_with(".prompt.txt")).collect();
        prompts.sort();
        for path in prompts {
            let prompt = std::fs::read_to_string(&path).unwrap();
            let text = std::sync::Arc::new(Mutex::new(String::new()));
            let sink = text.clone();
            let channel = Channel::new(move |body| {
                if let tauri::ipc::InvokeResponseBody::Json(json) = body {
                    if let Ok(Value::Object(e)) = serde_json::from_str::<Value>(&json) {
                        if e.get("type") == Some(&Value::from("text")) {
                            sink.lock().unwrap().push_str(e["text"].as_str().unwrap_or_default());
                        }
                    }
                }
                Ok(())
            });
            let summary = stream(&key, &model, "sample", &prompt, &channel, &Cancels::default()).await.map_err(|e| api_key::redact(&e, &key)).unwrap();
            let out = text.lock().unwrap().clone();
            let meta = format!(
                "<!-- model={} stop={:?} input={} cache_read={} cache_write={} output={} chars={} -->\n",
                summary.model, summary.stop_reason, summary.input_tokens, summary.cache_read_tokens,
                summary.cache_write_tokens, summary.output_tokens, out.chars().count()
            );
            let name = path.to_string_lossy().replace(".prompt.txt", &format!(".{model}.md"));
            std::fs::write(&name, meta + &out).unwrap();
            println!("{name}: {} chars, cache read {} / write {}", out.chars().count(), summary.cache_read_tokens, summary.cache_write_tokens);
        }
    }

    #[test]
    fn system_prompt_is_long_enough_to_cache() {
        // 512 tokens is the minimum cacheable prompt for Claude Sonnet 5.5 and Opus 5.5
        // (https://platform.claude.com/docs/en/build-with-claude/prompt-caching). Japanese text is
        // at least about one token per 1.5 characters, so 1,000 characters keeps a clear margin.
        assert!(SYSTEM_PROMPT.chars().count() >= 1000, "{} chars", SYSTEM_PROMPT.chars().count());
    }
}
