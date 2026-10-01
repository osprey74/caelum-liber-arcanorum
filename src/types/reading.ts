import type { DeckScope, DrawnCard } from "../lib/deck";

/** One position of a spread (src/data/spreads.json). x / y are the card center in card widths. */
export interface SpreadPosition {
  index: number;
  label: string;
  /** What this position means, e.g. "過去" or "財産・収入・価値観". */
  meaning: string;
  x: number;
  y: number;
  /** Extra rotation in degrees (Celtic Cross position 2 lies across position 1). */
  rotate?: number;
}

export interface Spread {
  id: "one" | "three" | "celtic" | "horoscope";
  name: string;
  name_en: string;
  description: string;
  positions: SpreadPosition[];
}

export interface CardMeaning {
  id: number;
  keywords_upright: string[];
  keywords_reversed: string[];
  upright: string;
  reversed: string;
  description: string;
}

export interface ReadingSettings {
  useReversed: boolean;
  scope: DeckScope;
  /** Sound effects for shuffling and turning cards. Optional for readings saved before it existed. */
  sound?: boolean;
}

/** A saved reading (history entry). */
export interface Reading {
  id: string;
  /** ISO 8601 timestamp. */
  createdAt: string;
  spreadId: Spread["id"];
  question: string;
  settings: ReadingSettings;
  cards: DrawnCard[];
}
