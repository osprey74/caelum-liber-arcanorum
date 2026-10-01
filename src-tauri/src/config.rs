//! App settings file (config.json), next to Liber Caeli's but in its own folder.
//!
//! Location (dirs::config_dir()):
//!   Windows: %APPDATA%\liber-arcanorum\config.json
//!   macOS:   ~/Library/Application Support/liber-arcanorum/config.json
//!   Linux:   $XDG_CONFIG_HOME/liber-arcanorum/config.json (or ~/.config/...)
//!
//! The API key itself is never written here (see api_key.rs); only whether one is saved and its last 4 characters.

use serde_json::{Map, Value};
use std::fs;
use std::path::PathBuf;

const APP_NAME: &str = "liber-arcanorum";

/// Model used when config.json does not name one. Any model ID may be written to the file by hand.
pub const DEFAULT_MODEL: &str = "claude-sonnet-5-5";

pub const KEY_SAVED: &str = "anthropic_api_key_saved";
pub const KEY_LAST4: &str = "anthropic_api_key_last4";
pub const MODEL: &str = "model";

fn config_dir() -> Option<PathBuf> {
    dirs::config_dir().map(|p| p.join(APP_NAME))
}

/// The whole file as a JSON object (empty when missing).
pub fn load() -> Result<Map<String, Value>, String> {
    let Some(path) = config_dir().map(|d| d.join("config.json")) else {
        return Ok(Map::new());
    };
    if !path.exists() {
        return Ok(Map::new());
    }
    let raw = fs::read_to_string(&path).map_err(|e| format!("read config.json failed: {e}"))?;
    match serde_json::from_str::<Value>(&raw).map_err(|e| format!("parse config.json failed: {e}"))? {
        Value::Object(map) => Ok(map),
        _ => Err("config.json is not a JSON object".to_string()),
    }
}

/// Reads the file, applies `change` and writes it back (keeps fields this app does not know about).
pub fn update(change: impl FnOnce(&mut Map<String, Value>)) -> Result<(), String> {
    let Some(dir) = config_dir() else {
        return Ok(());
    };
    let mut config = load()?;
    change(&mut config);
    fs::create_dir_all(&dir).map_err(|e| format!("create config dir failed: {e}"))?;
    let pretty = serde_json::to_string_pretty(&Value::Object(config))
        .map_err(|e| format!("serialize config.json failed: {e}"))?;
    fs::write(dir.join("config.json"), pretty).map_err(|e| format!("write config.json failed: {e}"))
}

/// The model ID to call: config.json's "model", or DEFAULT_MODEL.
pub fn model() -> String {
    load()
        .ok()
        .and_then(|c| c.get(MODEL).and_then(|v| v.as_str()).map(str::trim).map(str::to_string))
        .filter(|m| !m.is_empty())
        .unwrap_or_else(|| DEFAULT_MODEL.to_string())
}
