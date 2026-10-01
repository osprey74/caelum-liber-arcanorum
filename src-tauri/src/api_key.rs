//! Anthropic API key in the OS secure credential store (same approach as Liber Caeli, separate entry).
//!
//! Stored under:
//!   macOS:   Keychain (com.osprey74.liberarcanorum / anthropic_api_key)
//!   Windows: Credential Manager (DPAPI)
//!   Linux:   Secret Service (libsecret) via D-Bus
//!
//! The key never goes back to the frontend: it only learns whether one is saved and its last 4 characters.

use crate::config;
use keyring::Entry;
use serde_json::Value;

const SERVICE: &str = "com.osprey74.liberarcanorum";
const ACCOUNT: &str = "anthropic_api_key";

fn entry() -> Result<Entry, String> {
    Entry::new(SERVICE, ACCOUNT).map_err(|e| format!("keyring init failed: {e}"))
}

/// The saved key, or None.
pub fn get_api_key() -> Result<Option<String>, String> {
    match entry()?.get_password() {
        Ok(key) => Ok(Some(key)),
        Err(keyring::Error::NoEntry) => Ok(None),
        Err(e) => Err(format!("keyring get failed: {e}")),
    }
}

/// Saves the key and records "saved" and the last 4 characters in config.json.
pub fn set_api_key(key: &str) -> Result<(), String> {
    let trimmed = key.trim();
    if trimmed.is_empty() {
        return Err("API key is empty".to_string());
    }
    entry()?
        .set_password(trimmed)
        .map_err(|e| format!("keyring set failed: {e}"))?;
    let tail = last4(trimmed);
    config::update(|c| {
        c.insert(config::KEY_SAVED.to_string(), Value::Bool(true));
        c.insert(config::KEY_LAST4.to_string(), Value::String(tail));
    })
}

/// Removes the key and its metadata.
pub fn delete_api_key() -> Result<(), String> {
    match entry()?.delete_credential() {
        Ok(_) | Err(keyring::Error::NoEntry) => {}
        Err(e) => return Err(format!("keyring delete failed: {e}")),
    }
    config::update(|c| {
        c.remove(config::KEY_SAVED);
        c.remove(config::KEY_LAST4);
    })
}

pub fn last4(key: &str) -> String {
    let chars: Vec<char> = key.chars().collect();
    chars[chars.len().saturating_sub(4)..].iter().collect()
}

/// Removes the key from any text (error messages) before it leaves Rust.
pub fn redact(text: &str, key: &str) -> String {
    if key.len() < 8 {
        return text.to_string();
    }
    text.replace(key, &format!("****{}", last4(key)))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn last4_takes_the_tail() {
        assert_eq!(last4("sk-ant-api03-abcd1234"), "1234");
        assert_eq!(last4("ab"), "ab");
    }

    #[test]
    fn redact_hides_the_key() {
        let key = "sk-ant-api03-SECRETSECRET-wxyz";
        let msg = format!("request failed: header x-api-key: {key}");
        let out = redact(&msg, key);
        assert!(!out.contains("SECRET"));
        assert!(out.ends_with("****wxyz"));
    }
}
