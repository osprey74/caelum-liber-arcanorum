import type { Spread } from "../types/reading";

interface SpreadSchematicProps {
  spread: Spread;
  /** Box size in px. */
  width?: number;
  height?: number;
  active?: boolean;
}

/** A small diagram of the spread's layout, drawn from the same coordinates as the board (spreads.json). */
export function SpreadSchematic({ spread, width = 120, height = 90, active = false }: SpreadSchematicProps) {
  const rects = spread.positions.map((p) => {
    const sideways = (p.rotate ?? 0) % 180 !== 0;
    return { x: p.x, y: p.y, w: sideways ? 1.5 : 1, h: sideways ? 1 : 1.5, top: sideways };
  });
  const x0 = Math.min(...rects.map((r) => r.x - r.w / 2));
  const x1 = Math.max(...rects.map((r) => r.x + r.w / 2));
  const y0 = Math.min(...rects.map((r) => r.y - r.h / 2));
  const y1 = Math.max(...rects.map((r) => r.y + r.h / 2));
  // A single card would fill the box: cap the scale at about a third of the height per card.
  const scale = Math.min((width - 8) / (x1 - x0), (height - 8) / (y1 - y0), height / 3 / 1.5 * 1.1);
  const ox = (width - (x1 - x0) * scale) / 2 - x0 * scale;
  const oy = (height - (y1 - y0) * scale) / 2 - y0 * scale;

  return (
    <div className="relative" style={{ width, height }} aria-hidden="true">
      {rects.map((r, i) => (
        <div
          key={i}
          className={`absolute rounded-[2px] border border-gold ${r.top ? "bg-deep" : active ? "bg-gold/25" : "bg-gold/15"}`}
          style={{
            left: ox + (r.x - r.w / 2) * scale,
            top: oy + (r.y - r.h / 2) * scale,
            width: r.w * scale,
            height: r.h * scale,
            zIndex: r.top ? 1 : 0,
          }}
        />
      ))}
    </div>
  );
}
