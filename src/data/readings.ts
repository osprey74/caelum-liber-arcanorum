import type { CardMeaning, Spread } from "../types/reading";
import major from "./meanings/major.json";
import wands from "./meanings/wands.json";
import cups from "./meanings/cups.json";
import swords from "./meanings/swords.json";
import pentacles from "./meanings/pentacles.json";
import spreadsJson from "./spreads.json";

export const SPREADS = spreadsJson as Spread[];

const MEANINGS = new Map<number, CardMeaning>(
  ([...major, ...wands, ...cups, ...swords, ...pentacles] as CardMeaning[]).map((m) => [m.id, m]),
);

export function meaningOf(cardId: number): CardMeaning {
  const m = MEANINGS.get(cardId);
  if (!m) throw new Error(`meaning not found: ${cardId}`);
  return m;
}

export function spreadOf(id: Spread["id"]): Spread {
  const s = SPREADS.find((x) => x.id === id);
  if (!s) throw new Error(`spread not found: ${id}`);
  return s;
}
