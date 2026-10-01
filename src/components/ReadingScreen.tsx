import { useEffect, useRef, useState } from "react";
import { backImage } from "../data/cards";
import { spreadOf } from "../data/readings";
import { needsSafetyNotice } from "../lib/crisis";
import { playFlip, playShuffle } from "../lib/sound";
import type { Interpretation, Reading } from "../types/reading";
import { CardDetail } from "./CardDetail";
import { Icon } from "./Icon";
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
  // The interpretation opens beside the cards once they are all face up (the reader can close it again).
  const autoOpened = useRef(initialPanel);
  useEffect(() => {
    if (shuffling || next !== -1 || autoOpened.current) return;
    autoOpened.current = true;
    setPanelOpen(true);
  }, [shuffling, next]);
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

  const pill = "flex h-11 items-center gap-1.5 rounded-full px-[18px] text-sm transition";

  return (
    <div className="flex h-screen flex-col">
      <header className="flex items-center gap-6 border-b border-gold/20 px-8 py-4">
        <button type="button" onClick={onBack} className={`${pill} shrink-0 border border-gold/45 hover:bg-gold/10`}>
          <Icon name="back" className="h-4 w-4 text-gold" strokeWidth={2} />
          {fromHistory ? "履歴" : "ホーム"}
        </button>
        <div className="flex shrink-0 flex-col gap-0.5">
          <h1 className="font-display text-xl font-semibold tracking-[0.08em] text-gold">{spread.name}</h1>
          <p className="text-xs text-muted">
            {date} ・ {reading.settings.scope === "major" ? "大アルカナのみ" : "78枚"}
            {reading.settings.useReversed ? "" : " ・ 逆位置なし"}
          </p>
        </div>
        <p className="min-w-0 flex-1 truncate rounded-[10px] bg-deep px-[18px] py-2.5 text-sm text-soft" title={reading.question}>
          <span className="text-muted">問い</span>　{reading.question || "いまの自分に必要なこと"}
        </p>
        <div className="flex shrink-0 gap-2">
          {!shuffling && next !== -1 && (
            <>
              <button type="button" onClick={() => reveal(next)} className={`${pill} bg-gold font-medium text-night hover:brightness-110`}>
                次のカードをめくる（{next + 1}/{total}）
              </button>
              <button type="button" onClick={revealAll} className={`${pill} border border-gold/45 hover:bg-gold/10`}>
                すべてめくる
              </button>
            </>
          )}
          {!shuffling && next === -1 && (
            <button
              type="button"
              aria-pressed={panelOpen}
              onClick={() => setPanelOpen((v) => !v)}
              className={`${pill} ${panelOpen ? "border border-gold/45 hover:bg-gold/10" : "bg-gold font-medium text-night hover:brightness-110"}`}
            >
              {panelOpen ? "解釈を閉じる" : "解釈を読む"}
            </button>
          )}
        </div>
      </header>
      {needsSafetyNotice(reading.question) && <SafetyNotice />}

      <div className="relative flex min-h-0 flex-1">
      <main className="relative flex min-h-0 min-w-0 flex-1 flex-col p-8">
        {shuffling ? (
          <div className="flex h-full flex-col items-center justify-center gap-6" aria-live="polite">
            <div className="shuffle-stack">
              {[0, 1, 2, 3, 4].map((i) => (
                <img key={i} src={backImage("thumb")} alt="" className={`shuffle-card shuffle-card--${i}`} draggable={false} />
              ))}
            </div>
            <p className="text-soft">山札をシャッフルしています…</p>
          </div>
        ) : (
          <>
            <div className="min-h-0 flex-1">
              <SpreadBoard spread={spread} cards={reading.cards} revealed={revealed} onCardClick={onCardClick} />
            </div>
            <p className="pt-4 text-center text-[13px] text-muted">
              {next === -1 ? "カードを選ぶと、そのカードの意味を表示します" : "カードを選ぶとめくれます"}
            </p>
          </>
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
