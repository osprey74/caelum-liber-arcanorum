import { useEffect } from "react";
import { CARDS, plateName } from "../data/cards";
import { meaningOf } from "../data/readings";
import type { DrawnCard } from "../lib/deck";
import type { SpreadPosition } from "../types/reading";
import { TarotCard } from "./TarotCard";

interface CardDetailProps {
  drawn: DrawnCard;
  position: SpreadPosition;
  onClose: () => void;
}

/** Enlarged card with its meaning for the drawn orientation. */
export function CardDetail({ drawn, position, onClose }: CardDetailProps) {
  const card = CARDS[drawn.cardId];
  const m = meaningOf(drawn.cardId);
  const keywords = drawn.reversed ? m.keywords_reversed : m.keywords_upright;

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-6"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={plateName(card)}
    >
      <div
        className="flex max-h-full w-full max-w-5xl gap-8 overflow-auto rounded-xl border border-gold/30 bg-night p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="shrink-0">
          <TarotCard card={card} faceUp reversed={drawn.reversed} size="full" width={340} />
        </div>
        <div className="min-w-0 flex-1 space-y-4">
          <div>
            <p className="text-sm text-ivory/70">
              {position.index}. {position.label}
              {position.meaning !== position.label && <span>（{position.meaning}）</span>}
            </p>
            <h2 className="mt-1 text-2xl text-gold" style={{ fontFamily: '"Shippori Mincho", serif' }}>
              {plateName(card)}
              <span className="ml-3 text-base text-ivory/80">{drawn.reversed ? "逆位置" : "正位置"}</span>
            </h2>
          </div>
          <ul className="flex flex-wrap gap-2">
            {keywords.map((k) => (
              <li key={k} className="rounded-full border border-gold/40 px-3 py-0.5 text-sm text-gold">
                {k}
              </li>
            ))}
          </ul>
          <p className="leading-relaxed">{drawn.reversed ? m.reversed : m.upright}</p>
          <p className="border-t border-gold/20 pt-3 text-sm leading-relaxed text-ivory/70">{m.description}</p>
          <button
            type="button"
            onClick={onClose}
            className="rounded border border-gold/40 px-4 py-1.5 text-sm hover:bg-gold/10"
          >
            閉じる
          </button>
        </div>
      </div>
    </div>
  );
}
