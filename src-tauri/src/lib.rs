mod api_key;
mod config;
mod interpret;

use interpret::{AiConfig, Cancels, StreamEvent, Summary};
use serde_json::Value;
use tauri::ipc::Channel;
use tauri::State;

// --- Tauri commands (frontend ↔ settings / keyring / API). The key itself never crosses to the page. ---

#[tauri::command]
fn ai_get_config() -> Result<AiConfig, String> {
    interpret::ai_config()
}

#[tauri::command]
fn ai_set_model(model: String) -> Result<(), String> {
    let model = model.trim().to_string();
    if model.is_empty() {
        return Err("model is empty".to_string());
    }
    config::update(|c| {
        c.insert(config::MODEL.to_string(), Value::String(model));
    })
}

#[tauri::command]
fn keyring_set_api_key(key: String) -> Result<(), String> {
    api_key::set_api_key(&key)
}

#[tauri::command]
fn keyring_delete_api_key() -> Result<(), String> {
    api_key::delete_api_key()
}

#[tauri::command]
async fn interpret_reading(
    request_id: String,
    prompt: String,
    on_event: Channel<StreamEvent>,
    cancels: State<'_, Cancels>,
) -> Result<Summary, String> {
    interpret::run(&request_id, &prompt, &on_event, &cancels).await
}

#[tauri::command]
fn interpret_cancel(request_id: String, cancels: State<'_, Cancels>) {
    cancels.0.lock().unwrap().insert(request_id);
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .manage(Cancels::default())
        .invoke_handler(tauri::generate_handler![
            ai_get_config,
            ai_set_model,
            keyring_set_api_key,
            keyring_delete_api_key,
            interpret_reading,
            interpret_cancel,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
