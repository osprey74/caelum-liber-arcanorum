import { coinFlip, shuffle } from "./random";

export type DeckScope = "all" | "major";

export interface DrawnCard {
  cardId: number;
  reversed: boolean;
}

/** Card IDs in the deck: 0-77, or the Major Arcana 0-21 only. */
export function deckIds(scope: DeckScope): number[] {
  const n = scope === "major" ? 22 : 78;
  return Array.from({ length: n }, (_, i) => i);
}

/**
 * Shuffle the deck and draw `count` cards from the top. Each card is reversed with probability 1/2
 * when `useReversed` is true, otherwise always upright.
 */
export function drawCards(
  count: number,
  scope: DeckScope,
  useReversed: boolean,
  random: { shuffle: typeof shuffle; coinFlip: typeof coinFlip } = { shuffle, coinFlip },
): DrawnCard[] {
  const deck = random.shuffle(deckIds(scope));
  if (count > deck.length) throw new RangeError(`cannot draw ${count} cards from ${deck.length}`);
  return deck.slice(0, count).map((cardId) => ({
    cardId,
    reversed: useReversed ? random.coinFlip() : false,
  }));
}
