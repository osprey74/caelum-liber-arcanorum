import { useLayoutEffect, useRef, useState } from "react";
import { CARDS } from "../data/cards";
import type { DrawnCard } from "../lib/deck";
import type { Spread } from "../types/reading";
import { TarotCard } from "./TarotCard";

const CARD_H = 1.5; // card height in card widths (2:3)
const LABEL_H = 0.42; // room for the caption under each card (position, then card name), in card widths
const MAX_CARD_PX = 260;

interface SpreadBoardProps {
  spread: Spread;
  cards: DrawnCard[];
  /** Positions (0-based) already turned face up. */
  revealed: Set<number>;
  onCardClick: (position: number) => void;
}

/** Bounding box of the spread in card widths, including rotation and labels. */
function bounds(spread: Spread) {
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const p of spread.positions) {
    const sideways = (p.rotate ?? 0) % 180 !== 0;
    const w = sideways ? CARD_H : 1;
    const h = (sideways ? 1 : CARD_H) + LABEL_H;
    x0 = Math.min(x0, p.x - w / 2);
    x1 = Math.max(x1, p.x + w / 2);
    y0 = Math.min(y0, p.y - CARD_H / 2);
    y1 = Math.max(y1, p.y - CARD_H / 2 + h);
  }
  return { x0, y0, w: x1 - x0, h: y1 - y0 };
}

/** Card box of a position in card widths (a card lying sideways is 1.5 wide and 1 tall). */
function box(p: Spread["positions"][number]) {
  const sideways = (p.rotate ?? 0) % 180 !== 0;
  return { w: sideways ? CARD_H : 1, h: sideways ? 1 : CARD_H };
}

/**
 * True when no other card lies in the caption area under this card (as wide as the label row, 2.2 card widths,
 * and LABEL_H tall), so the card name can go under the position without running into a neighbour.
 */
function captionIsClear(spread: Spread, i: number): boolean {
  const p = spread.positions[i];
  const top = p.y + box(p).h / 2;
  const [x0, x1, y0, y1] = [p.x - 1.1, p.x + 1.1, top, top + LABEL_H];
  return spread.positions.every((q) => {
    if (q === p) return true;
    const b = box(q);
    return q.x + b.w / 2 <= x0 || q.x - b.w / 2 >= x1 || q.y + b.h / 2 <= y0 || q.y - b.h / 2 >= y1;
  });
}

/** Lays the cards out at the spread's coordinates, scaled to fit the available space. */
export function SpreadBoard({ spread, cards, revealed, onCardClick }: SpreadBoardProps) {
  const box = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ w: 800, h: 600 });

  useLayoutEffect(() => {
    const el = box.current;
    if (!el) return;
    const measure = () => setSize({ w: el.clientWidth, h: el.clientHeight });
    measure(); // before the first paint, so the cards never start off-center
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const b = bounds(spread);
  const unit = Math.min(size.w / b.w, size.h / b.h, MAX_CARD_PX); // px per card width
  const offsetX = (size.w - b.w * unit) / 2 - b.x0 * unit;
  const offsetY = (size.h - b.h * unit) / 2 - b.y0 * unit;

  // Positions stacked on the same spot (Celtic Cross 1 and 2) share one label row under the bottom card.
  const stacked = (i: number) =>
    spread.positions.filter((q) => q.x === spread.positions[i].x && q.y === spread.positions[i].y);

  return (
    <div ref={box} className="relative h-full w-full">
      {spread.positions.map((p, i) => {
        const drawn = cards[i];
        const card = CARDS[drawn.cardId];
        const faceUp = revealed.has(i);
        const cx = offsetX + p.x * unit;
        const cy = offsetY + p.y * unit;
        const labels = p.rotate ? [] : stacked(i);
        return (
          <div
            key={p.index}
            // The box itself stays upright; only the card inside turns. Clicks pass through the box so a
            // card lying across another one does not hide the card below.
            className="pointer-events-none absolute flex flex-col items-center"
            style={{
              left: cx - unit / 2,
              top: cy - (CARD_H * unit) / 2,
              width: unit,
              zIndex: p.rotate ? 2 : 1,
            }}
          >
            <div className="pointer-events-auto" style={{ transform: p.rotate ? `rotate(${p.rotate}deg)` : undefined }}>
              <TarotCard
                card={card}
                faceUp={faceUp}
                reversed={drawn.reversed}
                size={unit > 200 ? "medium" : "thumb"}
                width={unit}
                onClick={() => onCardClick(i)}
              />
            </div>
            {labels.length > 0 && (
              <div
                className="pointer-events-auto flex w-[220%] justify-center gap-3 text-muted"
                style={{ fontSize: Math.max(10, Math.min(13, unit * 0.075)), marginTop: Math.min(14, unit * 0.07) }}
              >
                {labels.map((q) => {
                  const j = spread.positions.indexOf(q);
                  const text = `${q.index} ・ ${q.label}`;
                  const drawnQ = cards[j];
                  // The card name goes under the position once face up, unless two positions share the row.
                  const named = labels.length === 1 && revealed.has(j) && captionIsClear(spread, j);
                  // Every label is clickable (turns the card, or opens it once face up), so a covered card in a
                  // stack can be reached the same way as any other.
                  return (
                    <button
                      key={q.index}
                      type="button"
                      onClick={() => onCardClick(j)}
                      title={q.meaning}
                      className="flex max-w-full flex-col items-center gap-0.5 rounded px-1 tracking-[0.12em] hover:text-gold"
                    >
                      <span className="truncate underline decoration-gold/30 underline-offset-2">{text}</span>
                      {named && (
                        <span className="truncate font-mincho tracking-normal text-ivory" style={{ fontSize: "1.15em" }}>
                          {CARDS[drawnQ.cardId].name_ja}
                          <span className="ml-1.5 text-soft" style={{ fontSize: "0.87em" }}>
                            {drawnQ.reversed ? "逆位置" : "正位置"}
                          </span>
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
