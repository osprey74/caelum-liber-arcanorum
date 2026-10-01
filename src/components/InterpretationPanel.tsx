import { useEffect, useRef, useState } from "react";
import { CARDS, plateName } from "../data/cards";
import { meaningOf, spreadOf } from "../data/readings";
import { aiAvailable, cancelInterpret, getAiConfig, interpret, modelName, type AiConfig, type InterpretSummary } from "../lib/ai";
import { needsSafetyNotice, SUPPORT_MARKER } from "../lib/crisis";
import { buildCopyText, buildPrompt } from "../lib/prompt";
import type { Interpretation, Reading } from "../types/reading";
import { AiSettingsDialog } from "./AiSettingsDialog";
import { Icon } from "./Icon";
import { Markdown } from "./Markdown";
import { SafetyNotice } from "./SafetyNotice";

interface InterpretationPanelProps {
  reading: Reading;
  /** A finished interpretation, to keep with the reading in the history. */
  onSaved: (interpretation: Interpretation) => void;
  /** The model judged the question to need the support screen. */
  onSupport: () => void;
  onClose: () => void;
}

type Status =
  | { kind: "idle" }
  | { kind: "streaming" }
  | { kind: "done"; summary?: InterpretSummary }
  | { kind: "error"; message: string };

/** The reading's text: the AI interpretation, or the card meanings (always available, also offline). */
export function InterpretationPanel({ reading, onSaved, onSupport, onClose }: InterpretationPanelProps) {
  const [tab, setTab] = useState<"ai" | "meanings">(reading.interpretation || aiAvailable ? "ai" : "meanings");
  const [text, setText] = useState(reading.interpretation?.text ?? "");
  const [model, setModel] = useState(reading.interpretation?.model ?? "");
  const [status, setStatus] = useState<Status>(reading.interpretation ? { kind: "done" } : { kind: "idle" });
  const [config, setConfig] = useState<AiConfig | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);
  const requestId = useRef<string | null>(null);

  useEffect(() => {
    if (aiAvailable) getAiConfig().then(setConfig).catch(() => setConfig(null));
  }, []);

  // Leaving the screen stops a running request.
  useEffect(
    () => () => {
      if (requestId.current) void cancelInterpret(requestId.current);
    },
    [],
  );

  const generate = async () => {
    const id = crypto.randomUUID();
    requestId.current = id;
    let full = "";
    setText("");
    setModel(config?.model ?? "");
    setStatus({ kind: "streaming" });
    try {
      const summary = await interpret(id, buildPrompt(reading), {
        onStart: setModel,
        onFallback: setModel,
        onText: (t) => {
          full += t;
          setText(full);
        },
      });
      if (requestId.current !== id) return;
      requestId.current = null;
      if (summary.cancelled) {
        setStatus({ kind: "idle" });
        setText("");
        return;
      }
      if (full.trim().startsWith(SUPPORT_MARKER)) {
        onSupport();
        return;
      }
      if (summary.stopReason === "refusal") {
        setText("");
        setStatus({ kind: "error", message: "この内容には、AIが解釈を控えました。「カードの意味」から結果をご覧いただけます。" });
        return;
      }
      setModel(summary.model);
      setStatus({ kind: "done", summary });
      onSaved({ text: full, model: summary.model, createdAt: new Date().toISOString() });
    } catch (e) {
      if (requestId.current !== id) return;
      requestId.current = null;
      setStatus({ kind: "error", message: String(e) });
    }
  };

  const stop = () => {
    if (requestId.current) void cancelInterpret(requestId.current);
  };

  const copy = async (label: string, value: string) => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(label);
      window.setTimeout(() => setCopied(null), 2000);
    } catch {
      setCopied("コピーできませんでした");
    }
  };

  // While streaming, hold the text back until it cannot be the support marker.
  const shown = status.kind === "streaming" && SUPPORT_MARKER.startsWith(text.trim().slice(0, SUPPORT_MARKER.length)) ? "" : text;
  const canGenerate = aiAvailable && config?.hasKey;
  const summary = status.kind === "done" ? status.summary : undefined;

  return (
    <aside className="flex h-full w-[min(460px,100vw)] shrink-0 flex-col border-l border-gold/25 bg-deep" aria-label="解釈">
      <div role="tablist" aria-label="表示の切り替え" className="flex items-center gap-1 border-b border-gold/20 px-5 pt-3.5">
        {(
          [
            ["ai", "AIによる解釈"],
            ["meanings", "カードの意味"],
          ] as const
        ).map(([value, label]) => (
          <button
            key={value}
            type="button"
            role="tab"
            aria-selected={tab === value}
            onClick={() => setTab(value)}
            className={`h-11 border-b-2 px-4 text-sm ${
              tab === value ? "border-gold font-medium text-gold" : "border-transparent text-muted hover:text-ivory"
            }`}
          >
            {label}
          </button>
        ))}
        <button type="button" onClick={onClose} className="ml-auto flex h-11 w-11 items-center justify-center text-muted hover:text-ivory" aria-label="解釈を閉じる">
          <Icon name="close" className="h-[18px] w-[18px]" />
        </button>
      </div>

      {needsSafetyNotice(reading.question) && <SafetyNotice />}
      <p className="bg-teal/[0.12] px-6 py-2.5 text-xs leading-[1.7] text-muted">
        占いは娯楽と内省のための読み物です。結果は未来を断定するものではありません。健康・お金・法律などの大切な判断は、専門家にご相談ください。
      </p>

      <div className="min-h-0 flex-1 overflow-y-auto px-7 py-5">
        {tab === "meanings" ? (
          <Meanings reading={reading} />
        ) : (
          <>
            {status.kind === "idle" && (
              <div className="space-y-4 text-sm leading-relaxed text-ivory/80">
                {!aiAvailable ? (
                  <p>AIによる解釈は、デスクトップアプリで利用できます。</p>
                ) : config && !config.hasKey ? (
                  <p>
                    AIによる解釈には、Anthropic の APIキーが必要です。
                    <button type="button" onClick={() => setSettingsOpen(true)} className="ml-1 text-gold underline underline-offset-2">
                      設定を開く
                    </button>
                  </p>
                ) : (
                  <p>引いたカードをもとに、AI がリーディングの文章を書きます（{modelName(config?.model ?? "")}）。</p>
                )}
                <p className="text-ivory/60">
                  APIキーがなくても、「プロンプトをコピー」でほかの AI に貼り付けて解釈を頼めます。カードごとの意味は「カードの意味」でご覧いただけます。
                </p>
              </div>
            )}
            {status.kind === "error" && <p className="rounded border border-red-300/40 bg-red-300/10 px-3 py-2 text-sm text-red-200">{status.message}</p>}
            {(status.kind === "streaming" || status.kind === "done") && (
              <>
                {status.kind === "streaming" && !shown && <p className="animate-pulse text-sm text-ivory/70">カードを読み解いています…</p>}
                <Markdown text={shown} />
                {status.kind === "streaming" && shown && <span className="ml-1 inline-block animate-pulse text-gold">▍</span>}
                {status.kind === "done" && (
                  <p className="mt-6 border-t border-gold/15 pt-2 text-[11px] text-muted">
                    {modelName(model)}
                    {reading.interpretation && !summary && ` ・ ${new Date(reading.interpretation.createdAt).toLocaleString("ja-JP")}`}
                    {summary &&
                      ` ・ 入力 ${summary.inputTokens + summary.cacheReadTokens + summary.cacheWriteTokens} トークン（キャッシュ読込 ${summary.cacheReadTokens}・書込 ${summary.cacheWriteTokens}）・ 出力 ${summary.outputTokens} トークン`}
                    {summary?.stopReason === "max_tokens" && " ・ 文章が長すぎたため途中で終わっています"}
                  </p>
                )}
              </>
            )}
          </>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-2.5 border-t border-gold/20 px-6 py-4">
        {tab === "ai" && status.kind === "streaming" ? (
          <button type="button" onClick={stop} className="h-11 rounded-full border border-ivory/30 px-5 text-sm hover:bg-ivory/10">
            停止
          </button>
        ) : (
          tab === "ai" && (
            <button
              type="button"
              disabled={!canGenerate}
              onClick={generate}
              className="h-11 rounded-full bg-gold px-5 text-sm font-medium text-night hover:brightness-110 disabled:opacity-40"
            >
              {status.kind === "done" || status.kind === "error" ? "もう一度解釈する" : "AIで解釈する"}
            </button>
          )
        )}
        {tab === "ai" && status.kind === "done" && (
          <button type="button" onClick={() => copy("解釈をコピーしました", text)} className="h-11 rounded-full border border-gold/45 px-4 text-sm hover:bg-gold/10">
            解釈をコピー
          </button>
        )}
        <button
          type="button"
          onClick={() => copy("プロンプトをコピーしました", buildCopyText(reading))}
          className="h-11 rounded-full border border-gold/45 px-4 text-sm hover:bg-gold/10"
        >
          プロンプトをコピー
        </button>
        {aiAvailable && (
          <button type="button" onClick={() => setSettingsOpen(true)} className="ml-auto text-sm text-ivory/60 hover:text-ivory">
            AIの設定
          </button>
        )}
        {copied && <span className="w-full text-xs text-teal">{copied}</span>}
      </div>

      {settingsOpen && (
        <AiSettingsDialog
          onClose={(c) => {
            setSettingsOpen(false);
            if (c) setConfig(c);
          }}
        />
      )}
    </aside>
  );
}

/** The phase 3 meanings for each position: the reading without the API. */
function Meanings({ reading }: { reading: Reading }) {
  const spread = spreadOf(reading.spreadId);
  return (
    <div className="space-y-5">
      {spread.positions.map((p, i) => {
        const drawn = reading.cards[i];
        const m = meaningOf(drawn.cardId);
        const keywords = drawn.reversed ? m.keywords_reversed : m.keywords_upright;
        return (
          <section key={p.index}>
            <p className="text-xs text-ivory/60">
              {p.index}. {p.label}
              {p.meaning !== p.label && `（${p.meaning}）`}
            </p>
            <h4 className="font-display font-semibold text-gold">
              {plateName(CARDS[drawn.cardId])}
              <span className="ml-2 text-sm text-ivory/75">{drawn.reversed ? "逆位置" : "正位置"}</span>
            </h4>
            <p className="mt-1 text-xs text-gold/80">{keywords.join("・")}</p>
            <p className="mt-1 font-mincho text-[15px] leading-[1.9]">{drawn.reversed ? m.reversed : m.upright}</p>
          </section>
        );
      })}
    </div>
  );
}
