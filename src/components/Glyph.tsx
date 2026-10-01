// Planet, zodiac and element symbols drawn as SVG (not as font characters): the alchemical
// element symbols are missing from most system fonts, and zodiac signs may render as colour emoji.
// All paths are original drawings on a 24 x 24 grid, stroked (see README "記号の SVG").

type GlyphDef = { name: string; d: string };

export const GLYPHS: Record<string, GlyphDef> = {
  // planets
  "☉": { name: "太陽", d: "M12 4a8 8 0 1 0 0.01 0Z M12 10.6a1.4 1.4 0 1 0 0.01 0Z" },
  "☽": { name: "月", d: "M14.5 3.5a8.5 8.5 0 1 0 0 17a7 7 0 0 1 0-17Z" },
  "☿": { name: "水星", d: "M8.5 3a3.5 3.5 0 0 0 7 0 M12 6.5a4 4 0 1 0 0.01 0Z M12 14.5V21 M9 18h6" },
  "♀": { name: "金星", d: "M12 3.5a5 5 0 1 0 0.01 0Z M12 13.5V21 M8.8 17.5h6.4" },
  "♂": { name: "火星", d: "M10 9.5a5 5 0 1 0 0.01 0Z M13.6 10.9L19.5 5 M14.8 5h4.7v4.7" },
  "♃": { name: "木星", d: "M6 8.2c0-3.6 5.4-4.4 5.4-0.6c0 3-3.4 6.2-5.4 8.4H19 M15.5 4.5V21" },
  "♄": { name: "土星", d: "M8.5 3v14 M5.5 6h6 M8.5 11.5c1.8-2.6 7-2.4 7 1.6c0 2.8-3 3.6-2.6 7.4" },
  // zodiac
  "♈": { name: "牡羊座", d: "M12 20.5V9.5C12 5.5 10 3.5 7.5 3.5C5.5 3.5 4.3 5 4.3 6.8C4.3 8.3 5.3 9.4 6.6 9.4 M12 9.5C12 5.5 14 3.5 16.5 3.5C18.5 3.5 19.7 5 19.7 6.8C19.7 8.3 18.7 9.4 17.4 9.4" },
  "♉": { name: "牡牛座", d: "M12 10.5a5 5 0 1 0 0.01 0Z M4.5 4c1 4 4 6.5 7.5 6.5S18.5 8 19.5 4" },
  "♊": { name: "双子座", d: "M5.5 4.5c4 1.2 9 1.2 13 0 M5.5 19.5c4-1.2 9-1.2 13 0 M9 5.4v13.2 M15 5.4v13.2" },
  "♋": { name: "蟹座", d: "M7 7a2.4 2.4 0 1 0 0.01 0Z M7 7c4-1.8 9.5-1.6 13 1.5 M17 12.2a2.4 2.4 0 1 0 0.01 0Z M17 17c-4 1.8-9.5 1.6-13-1.5" },
  "♌": { name: "獅子座", d: "M8 12.5a3 3 0 1 0 0.01 0Z M11 15.5C11 9.5 8.5 7.8 9.5 5.3C10.5 3 15.3 3 16.3 5.8C17.6 9.5 13.5 13.5 14.2 17.8C14.7 20.6 17.6 21.2 19.5 19" },
  "♍": { name: "乙女座", d: "M4 6.5c1.2 0 2 0.8 2 2V18 M6 9c0-3 4-3 4 0v9 M10 9c0-3 4-3 4 0v6.5c0 3.2 3.6 4.2 5.2 1.5c1-1.8-0.4-4-3-3.2" },
  "♎": { name: "天秤座", d: "M4 19.5h16 M4 15.5h5c-2-1.6-2-4.8 0.2-6.2c1.6-1.1 4-1.1 5.6 0c2.2 1.4 2.2 4.6 0.2 6.2h5" },
  "♏": { name: "蠍座", d: "M4 6.5c1.2 0 2 0.8 2 2V18 M6 9c0-3 4-3 4 0v9 M10 9c0-3 4-3 4 0v8.2c0 1.7 1.2 2.5 3 2.5h2 M17.2 17.5l2.3 2.2l-2.3 2.2" },
  "♐": { name: "射手座", d: "M5 19L19 5 M12.5 5H19v6.5 M8 11l5 5" },
  "♑": { name: "山羊座", d: "M4 6.5c1.6 0 2.6 1.2 3 2.6L9 17l3-9.5c0.8-2.3 3.5-2 3.5 1v5c0 3.6 3.4 4.6 4.4 2.3c1-2.3-1.8-4-3.8-2c-1.4 1.4-2.6 4.7-5 5.7" },
  "♒": { name: "水瓶座", d: "M3 10.5l3-2.5l3 2.5l3-2.5l3 2.5l3-2.5l3 2.5 M3 16.5l3-2.5l3 2.5l3-2.5l3 2.5l3-2.5l3 2.5" },
  "♓": { name: "魚座", d: "M6.5 4c3.5 4 3.5 12 0 16 M17.5 4c-3.5 4-3.5 12 0 16 M5 12h14" },
  // alchemical elements
  "🜂": { name: "火", d: "M12 4.5l8 14.5H4Z" },
  "🜄": { name: "水", d: "M4 5h16l-8 14.5Z" },
  "🜁": { name: "風", d: "M12 4.5l8 14.5H4Z M6.4 14.4h11.2" },
  "🜃": { name: "地", d: "M4 5h16l-8 14.5Z M6.4 9.6h11.2" },
};

/** Split a glyph string into its symbols (handles the astral-plane alchemical characters). */
export function splitGlyphs(glyph: string): string[] {
  return Array.from(glyph).filter((ch) => ch.trim() !== "" && ch !== "︎" && ch !== "️");
}

interface GlyphProps {
  symbol: string;
  className?: string;
  strokeWidth?: number;
}

export function Glyph({ symbol, className, strokeWidth = 1.6 }: GlyphProps) {
  const def = GLYPHS[symbol];
  if (!def) return null;
  return (
    <svg
      viewBox="0 0 24 24"
      className={className}
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      role="img"
      aria-label={def.name}
    >
      <path d={def.d} />
    </svg>
  );
}
