import type { CardData, CardSize } from "../types/card";
import cardsJson from "./cards.json";

export const CARDS = cardsJson as CardData[];

// Image URLs resolved by Vite. Keys look like "../assets/cards/full/00.webp".
const imageUrls = import.meta.glob("../assets/cards/*/*.webp", {
  eager: true,
  query: "?url",
  import: "default",
}) as Record<string, string>;

function url(path: string): string {
  const resolved = imageUrls[`../assets/${path}`];
  if (!resolved) throw new Error(`card image not found: ${path}`);
  return resolved;
}

export function cardImage(card: CardData, size: CardSize): string {
  return url(card.images[size]);
}

export function backImage(size: CardSize): string {
  return url(`cards/${size}/back.webp`);
}

/** Name shown on the plate: "XVII 星" for the Major Arcana, the Japanese name otherwise. */
export function plateName(card: CardData): string {
  return card.roman !== undefined ? `${card.roman} ${card.name_ja}` : card.name_ja;
}
