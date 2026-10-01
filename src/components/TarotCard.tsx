import type { CSSProperties } from "react";
import { backImage, cardImage, plateName } from "../data/cards";
import type { CardData, CardSize } from "../types/card";
import { Glyph, splitGlyphs } from "./Glyph";
import "./TarotCard.css";

// Overlay positions measured on tools/tarot-gen/refs/frame.png (1024 x 1536), as fractions of the card.
const MEDALLION = { cx: 511.5 / 1024, cy: 139 / 1536, d: 160 / 1024 };
const PLATE = { x0: 263 / 1024, y0: 1310 / 1536, x1: 760 / 1024, y1: 1424 / 1536 };

/** Default display width (CSS px) for each image size. */
const DEFAULT_WIDTH: Record<CardSize, number> = { full: 480, medium: 300, thumb: 150 };

interface TarotCardProps {
  card: CardData;
  /** true: the face is shown; false: the back. Changing it plays the flip animation. */
  faceUp: boolean;
  /** Reversed position: the whole card, overlays included, is turned 180 degrees. */
  reversed?: boolean;
  size?: CardSize;
  /** Display width in CSS px (defaults to the size's width). */
  width?: number;
  /** CSS font-family for the name plate (the bundled faces are declared in styles.css). */
  plateFont?: string;
  onClick?: () => void;
}

/** Thumbnails get 15% larger plate text and glyphs so they stay legible (approved 2026-10-01). */
const THUMB_SCALE = 1.15;

/** Plate text size in container-query units: `scale` x the base size, shrunk so long names stay
 * inside the plate. */
function plateFontSize(text: string, scale: number): number {
  // Full-width characters take about 1em, Latin letters / digits / spaces about 0.62em.
  const units = Array.from(text).reduce((n, ch) => n + (ch.charCodeAt(0) < 0x2000 ? 0.62 : 1), 0);
  const plateWidth = (PLATE.x1 - PLATE.x0) * 100 * 0.84;
  return Math.min(5.0 * scale, plateWidth / units);
}

export function TarotCard({
  card,
  faceUp,
  reversed = false,
  size = "medium",
  width,
  plateFont,
  onClick,
}: TarotCardProps) {
  const name = plateName(card);
  const glyphs = splitGlyphs(card.glyph);
  const style = {
    width: width ?? DEFAULT_WIDTH[size],
    // Card width = 100cqw, height = 150cqw (2:3), so every position is in container-width units.
    "--medallion-x": `${(MEDALLION.cx - MEDALLION.d / 2) * 100}cqw`,
    "--medallion-y": `${(MEDALLION.cy * 1.5 - MEDALLION.d / 2) * 100}cqw`,
    "--medallion-d": `${MEDALLION.d * 100}cqw`,
    "--plate-x": `${PLATE.x0 * 100}cqw`,
    "--plate-y": `${PLATE.y0 * 150}cqw`,
    "--plate-w": `${(PLATE.x1 - PLATE.x0) * 100}cqw`,
    "--plate-h": `${(PLATE.y1 - PLATE.y0) * 150}cqw`,
    "--plate-font-size": `${plateFontSize(name, size === "thumb" ? THUMB_SCALE : 1)}cqw`,
    "--glyph-scale": size === "thumb" ? THUMB_SCALE : 1,
    ...(plateFont ? { "--plate-font": plateFont } : {}),
  } as CSSProperties;

  const Tag = onClick ? "button" : "div";
  return (
    <Tag
      type={onClick ? "button" : undefined}
      className="tarot-card"
      style={style}
      onClick={onClick}
      aria-label={faceUp ? `${name}${reversed ? "（逆位置）" : ""}` : "カードの裏面"}
    >
      <div className={`tarot-card__turn${reversed ? " is-reversed" : ""}`}>
        <div className={`tarot-card__flip${faceUp ? " is-face-up" : ""}`}>
          <div className="tarot-card__side tarot-card__front">
            <img src={cardImage(card, size)} alt="" draggable={false} />
            <div className={`tarot-card__medallion count-${glyphs.length}`}>
              {glyphs.map((g, i) => (
                <Glyph key={i} symbol={g} className="tarot-card__glyph" />
              ))}
            </div>
            <div className="tarot-card__plate">
              <span>{name}</span>
            </div>
          </div>
          <div className="tarot-card__side tarot-card__back">
            <img src={backImage(size)} alt="" draggable={false} />
          </div>
        </div>
      </div>
    </Tag>
  );
}
