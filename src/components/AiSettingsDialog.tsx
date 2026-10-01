import { useEffect, useState } from "react";
import { deleteApiKey, getAiConfig, MODELS, saveApiKey, setAiModel, type AiConfig } from "../lib/ai";

interface AiSettingsDialogProps {
  onClose: (config: AiConfig | null) => void;
}

/** API key (kept in the OS credential store) and the model. */
export function AiSettingsDialog({ onClose }: AiSettingsDialogProps) {
  const [config, setConfig] = useState<AiConfig | null>(null);
  const [key, setKey] = useState("");
  const [message, setMessage] = useState<{ text: string; error?: boolean } | null>(null);
  const [busy, setBusy] = useState(false);

  const reload = () =>
    getAiConfig()
      .then(setConfig)
      .catch((e) => setMessage({ text: `設定を読み込めませんでした：${e}`, error: true }));

  useEffect(() => {
    void reload();
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose(config);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose, config]);

  const run = async (action: () => Promise<void>, done: string) => {
    setBusy(true);
    setMessage(null);
    try {
      await action();
      await reload();
      setMessage({ text: done });
    } catch (e) {
      setMessage({ text: String(e), error: true });
    } finally {
      setBusy(false);
    }
  };

  const custom = config && !MODELS.some((m) => m.id === config.model);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-6" role="dialog" aria-modal="true" aria-label="AIの設定">
      <div className="w-full max-w-lg rounded-2xl border border-gold/30 bg-panel p-7 shadow-2xl">
        <h2 className="font-display text-xl font-semibold tracking-[0.06em] text-gold">AIによる解釈の設定</h2>

        <section className="mt-5">
          <h3 className="text-sm text-ivory/80">Anthropic APIキー</h3>
          <p className="mt-1 text-xs leading-relaxed text-ivory/60">
            キーは OS の資格情報ストア（Windows の資格情報マネージャー、macOS のキーチェーン）に保存され、画面やファイルには残りません。Liber Caeli
            とは別に保存されます。
          </p>
          <p className="mt-2 text-sm">
            {config === null ? "確認しています…" : config.hasKey ? `保存済み（末尾 ${config.keyLast4 ?? "????"}）` : "未設定"}
          </p>
          <div className="mt-2 flex gap-2">
            <input
              type="password"
              value={key}
              onChange={(e) => setKey(e.target.value)}
              placeholder="sk-ant-..."
              autoComplete="off"
              spellCheck={false}
              className="min-w-0 flex-1 rounded border border-gold/30 bg-night/60 px-3 py-1.5 text-sm focus:border-gold focus:outline-none"
            />
            <button
              type="button"
              disabled={busy || !key.trim()}
              onClick={() => run(() => saveApiKey(key).then(() => setKey("")), "APIキーを保存しました")}
              className="rounded bg-gold px-4 py-1.5 text-sm text-night disabled:opacity-40"
            >
              保存
            </button>
            {config?.hasKey && (
              <button
                type="button"
                disabled={busy}
                onClick={() => run(deleteApiKey, "APIキーを削除しました")}
                className="rounded border border-ivory/30 px-3 py-1.5 text-sm hover:bg-ivory/10 disabled:opacity-40"
              >
                削除
              </button>
            )}
          </div>
        </section>

        <section className="mt-6">
          <h3 className="text-sm text-ivory/80">モデル</h3>
          <div className="mt-2 space-y-2">
            {MODELS.map((m) => (
              <label key={m.id} className="flex items-start gap-2 text-sm">
                <input
                  type="radio"
                  name="model"
                  checked={config?.model === m.id}
                  disabled={busy || !config}
                  onChange={() => run(() => setAiModel(m.id), `${m.name} に切り替えました`)}
                  className="mt-1 accent-gold"
                />
                <span>
                  {m.name}
                  <span className="block text-xs text-ivory/60">{m.note}</span>
                </span>
              </label>
            ))}
            {custom && <p className="text-xs text-ivory/60">設定ファイルで指定されたモデル：{config.model}</p>}
          </div>
          <p className="mt-2 text-xs leading-relaxed text-ivory/50">
            1回の解釈の料金の目安：Sonnet 5.5 で約2〜4円（2026-10 の実測）、Opus 5.5 で約8〜16円（推測）。スプレッドの枚数と文章の長さで変わります。
          </p>
        </section>

        {message && <p className={`mt-4 text-sm ${message.error ? "text-red-300" : "text-teal"}`}>{message.text}</p>}

        <div className="mt-6 flex justify-end">
          <button type="button" onClick={() => onClose(config)} className="rounded border border-gold/40 px-4 py-1.5 text-sm hover:bg-gold/10">
            閉じる
          </button>
        </div>
      </div>
    </div>
  );
}
