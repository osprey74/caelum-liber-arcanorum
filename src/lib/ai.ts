// Frontend side of the Claude API: settings and the streamed interpretation. The API key stays in Rust
// (src-tauri/src/api_key.rs, interpret.rs); the page only sends the reading and receives text.
import { Channel, invoke, isTauri } from "@tauri-apps/api/core";

/** Models offered in the settings (names and prices checked on 2026-10-01 on
 *  https://platform.claude.com/docs/en/about-claude/pricing and .../about-claude/models/overview). */
export const MODELS = [
  { id: "claude-sonnet-5-5", name: "Claude Sonnet 5.5", note: "標準・速い（入力 $2 / 出力 $10、100万トークンあたり）" },
  { id: "claude-opus-5-5", name: "Claude Opus 5.5", note: "高性能（入力 $4 / 出力 $20、100万トークンあたり）" },
] as const;

export interface AiConfig {
  model: string;
  hasKey: boolean;
  keyLast4: string | null;
}

export interface InterpretSummary {
  model: string;
  stopReason: string | null;
  inputTokens: number;
  outputTokens: number;
  cacheReadTokens: number;
  cacheWriteTokens: number;
  cancelled: boolean;
}

type StreamEvent =
  | { type: "start"; model: string }
  | { type: "text"; text: string }
  | { type: "fallback"; to: string };

/** False in a plain browser (vite dev without Tauri): the AI features are then unavailable. */
export const aiAvailable = isTauri();

export function getAiConfig(): Promise<AiConfig> {
  return invoke<AiConfig>("ai_get_config");
}

export function setAiModel(model: string): Promise<void> {
  return invoke("ai_set_model", { model });
}

export function saveApiKey(key: string): Promise<void> {
  return invoke("keyring_set_api_key", { key });
}

export function deleteApiKey(): Promise<void> {
  return invoke("keyring_delete_api_key");
}

export interface InterpretHandlers {
  onStart?: (model: string) => void;
  onText: (text: string) => void;
  onFallback?: (to: string) => void;
}

/** Streams the interpretation of `prompt`; resolves when the answer is complete (or cancelled). */
export function interpret(requestId: string, prompt: string, handlers: InterpretHandlers): Promise<InterpretSummary> {
  const onEvent = new Channel<StreamEvent>();
  onEvent.onmessage = (e) => {
    if (e.type === "text") handlers.onText(e.text);
    else if (e.type === "start") handlers.onStart?.(e.model);
    else handlers.onFallback?.(e.to);
  };
  return invoke<InterpretSummary>("interpret_reading", { requestId, prompt, onEvent });
}

export function cancelInterpret(requestId: string): Promise<void> {
  return invoke("interpret_cancel", { requestId });
}

export function modelName(id: string): string {
  return MODELS.find((m) => m.id === id)?.name ?? id;
}
