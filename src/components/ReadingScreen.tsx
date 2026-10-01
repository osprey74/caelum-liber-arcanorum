import { useEffect, useState } from "react";
import { backImage } from "../data/cards";
import { spreadOf } from "../data/readings";
import { needsSafetyNotice } from "../lib/crisis";
import { playFlip, playShuffle } from "../lib/sound";
import type { Interpretation, Reading } from "../types/reading";
import { CardDetail } from "./CardDetail";
import { InterpretationPanel } from "./InterpretationPanel";
import { SafetyNotice } from "./SafetyNotice";
import { SpreadBoard } from "./SpreadBoard";
import "./ReadingScreen.css";

interface ReadingScreenProps {
  reading: Reading;
  /** Opened from the history: every card starts face up and no shuffle is shown. */
  fromHistory?: boolean;
  /** Position whose detail is open at first (development screenshots). */
  initialDetail?: number;
  /** Open the interpretation panel at first (development screenshots). */
  initialPanel?: boolean;
  /** The reading changed (an interpretation was added): save it. */
  onUpdate: (reading: Reading) => void;
  /** The question needs the support screen instead of a reading. */
  onSupport: () => void;
  onBack: () => void;
}

const SHUFFLE_MS = 1400;

export function ReadingScreen({
  reading: initial,
  fromHistory = false,
  initialDetail,
  initialPanel = false,
  onUpdate,
  onSupport,
  onBack,
}: ReadingScreenProps) {
  const [reading, setReading] = useState(initial);
  const spread = spreadOf(reading.spreadId);
  const total = spread.positions.length;
  const [shuffling, setShuffling] = useState(!fromHistory);
  const [revealed, setRevealed] = useState<Set<number>>(
    () => new Set(fromHistory ? spread.positions.map((_, i) => i) : []),
  );
  const [detail, setDetail] = useState<number | null>(initialDetail ?? null);
  const [panelOpen, setPanelOpen] = useState(initialPanel);

  useEffect(() => {
    if (!shuffling) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!reduce) playShuffle(SHUFFLE_MS / 1000);
    const t = window.setTimeout(() => setShuffling(false), reduce ? 0 : SHUFFLE_MS);
    return () => window.clearTimeout(t);
  }, [shuffling]);

  const next = spread.positions.findIndex((_, i) => !revealed.has(i));
  const reveal = (i: number) => {
    if (revealed.has(i)) return;
    playFlip();
    setRevealed((prev) => new Set(prev).add(i));
  };
  const revealAll = () => {
    if (next === -1) return;
    playFlip();
    setRevealed(new Set(spread.positions.map((_, i) => i)));
  };
  const saveInterpretation = (interpretation: Interpretation) => {
    const next = { ...reading, interpretation };
    setReading(next);
    onUpdate(next);
  };
  const onCardClick = (i: number) => (revealed.has(i) ? setDetail(i) : reveal(i));
  const date = new Date(reading.createdAt).toLocaleString("ja-JP", { dateStyle: "medium", timeStyle: "short" });

  return (
    <div className="flex h-screen flex-col">
      <header className="flex flex-wrap items-center gap-x-6 gap-y-2 border-b border-gold/20 px-6 py-3">
        <button type="button" onClick={onBack} className="rounded border border-gold/40 px-3 py-1 text-sm hover:bg-gold/10">
          ← 戻る
        </button>
        <div>
          <h1 className="text-lg text-gold">{spread.name}</h1>
          <p className="text-xs text-ivory/60">
            {date}・{reading.settings.scope === "major" ? "大アルカナのみ" : "78枚"}
            {reading.settings.useReversed ? "" : "・逆位置なし"}
          </p>
        </div>
        {reading.question && (
          <p className="min-w-0 flex-1 truncate text-sm text-ivory/85" title={reading.question}>
            問い：{reading.question}
          </p>
        )}
        <div className="ml-auto flex gap-2">
          {!shuffling && next !== -1 && (
            <>
              <button type="button" onClick={() => reveal(next)} className="rounded bg-gold px-4 py-1.5 text-sm text-night hover:brightness-110">
                次のカードをめくる（{next + 1}/{total}）
              </button>
              <button
                type="button"
                onClick={revealAll}
                className="rounded border border-gold/40 px-3 py-1.5 text-sm hover:bg-gold/10"
              >
                すべてめくる
              </button>
            </>
          )}
          {!shuffling && next === -1 && (
            <>
              <p className="self-center text-sm text-ivory/70">カードをクリックすると意味を表示します</p>
              <button
                type="button"
                onClick={() => setPanelOpen((v) => !v)}
                className="rounded bg-gold px-4 py-1.5 text-sm text-night hover:brightness-110"
              >
                {panelOpen ? "解釈を閉じる" : "解釈を読む"}
              </button>
            </>
          )}
        </div>
      </header>
      {needsSafetyNotice(reading.question) && <SafetyNotice />}

      <div className="relative flex min-h-0 flex-1">
      <main className="relative min-h-0 min-w-0 flex-1 p-6">
        {shuffling ? (
          <div className="flex h-full flex-col items-center justify-center gap-6" aria-live="polite">
            <div className="shuffle-stack">
              {[0, 1, 2, 3, 4].map((i) => (
                <img key={i} src={backImage("thumb")} alt="" className={`shuffle-card shuffle-card--${i}`} draggable={false} />
              ))}
            </div>
            <p className="text-ivory/80">山札をシャッフルしています…</p>
          </div>
        ) : (
          <SpreadBoard spread={spread} cards={reading.cards} revealed={revealed} onCardClick={onCardClick} />
        )}
      </main>
      {panelOpen && (
        <InterpretationPanel
          reading={reading}
          onSaved={saveInterpretation}
          onSupport={onSupport}
          onClose={() => setPanelOpen(false)}
        />
      )}
      </div>

      {detail !== null && (
        <CardDetail drawn={reading.cards[detail]} position={spread.positions[detail]} onClose={() => setDetail(null)} />
      )}
    </div>
  );
}
