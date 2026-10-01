import type { Reading, ReadingSettings } from "../types/reading";

// Saved in the webview's localStorage (kept per app in the OS app-data folder by Tauri).
const HISTORY_KEY = "liber-arcanorum.history.v1";
const SETTINGS_KEY = "liber-arcanorum.settings.v1";
const HISTORY_LIMIT = 500;

export const DEFAULT_SETTINGS: ReadingSettings = { useReversed: true, scope: "all", sound: true };

function read<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

function write(key: string, value: unknown): boolean {
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    return false;
  }
}

export function loadHistory(): Reading[] {
  const list = read<Reading[]>(HISTORY_KEY, []);
  return Array.isArray(list) ? list : [];
}

/** Newest first; the oldest entries are dropped beyond HISTORY_LIMIT. */
export function saveReading(reading: Reading): boolean {
  const list = [reading, ...loadHistory().filter((r) => r.id !== reading.id)].slice(0, HISTORY_LIMIT);
  return write(HISTORY_KEY, list);
}

export function deleteReading(id: string): boolean {
  return write(HISTORY_KEY, loadHistory().filter((r) => r.id !== id));
}

export function loadSettings(): ReadingSettings {
  return { ...DEFAULT_SETTINGS, ...read<Partial<ReadingSettings>>(SETTINGS_KEY, {}) };
}

export function saveSettings(settings: ReadingSettings): boolean {
  return write(SETTINGS_KEY, settings);
}
