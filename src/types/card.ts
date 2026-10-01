export type Suit = "wands" | "cups" | "swords" | "pentacles";
export type CardSize = "full" | "medium" | "thumb";

/** One entry of src/data/cards.json (written by tools/tarot-gen/build_assets.py). */
export interface CardData {
  id: number;
  slug: string;
  arcana: "major" | "minor";
  name_en: string;
  name_ja: string;
  /** Planet / sign / element symbols shown in the medallion, e.g. "☿", "🜂", "♂♈". */
  glyph: string;
  /** Major Arcana only, e.g. "XVII". */
  roman?: string;
  suit?: Suit;
  rank?: number | "page" | "knight" | "queen" | "king";
  type?: "ace" | "pip" | "court";
  decan?: { planet: string; sign: string; decan_no: number };
  images: Record<CardSize, string>;
}
