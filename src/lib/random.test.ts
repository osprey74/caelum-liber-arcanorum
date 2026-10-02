import { describe, expect, it } from "vitest";
import { drawCards, deckIds } from "./deck";
import { coinFlip, randomInt, shuffle } from "./random";

// Chi-square critical values at p = 0.001 (a correct implementation fails about 1 in 1000 runs).
const CHI2_P001: Record<number, number> = { 1: 10.83, 9: 27.88, 21: 46.8, 77: 117.0 };

function chiSquare(observed: number[], expected: number): number {
  return observed.reduce((s, o) => s + (o - expected) ** 2 / expected, 0);
}

describe("randomInt", () => {
  it("stays in range", () => {
    for (let i = 0; i < 10000; i++) {
      const v = randomInt(78);
      expect(v).toBeGreaterThanOrEqual(0);
      expect(v).toBeLessThan(78);
      expect(Number.isInteger(v)).toBe(true);
    }
  });

  it("rejects values in the incomplete last block (no modulo bias)", () => {
    // max = 3: limit = 2^32 - (2^32 mod 3) = 4294967295. The first value is rejected.
    const values = [4294967295, 7];
    const source = (buf: Uint32Array) => {
      buf[0] = values.shift()!;
      return buf;
    };
    expect(randomInt(3, source)).toBe(7 % 3);
  });

  it("is roughly uniform", () => {
    const n = 10, trials = 100000;
    const counts = new Array(n).fill(0);
    for (let i = 0; i < trials; i++) counts[randomInt(n)]++;
    expect(chiSquare(counts, trials / n)).toBeLessThan(CHI2_P001[9]);
  });

  it("rejects invalid bounds", () => {
    expect(() => randomInt(0)).toThrow(RangeError);
    expect(() => randomInt(1.5)).toThrow(RangeError);
  });
});

// Tens of thousands of shuffles: a few seconds here, longer on CI runners (8.6 s seen on GitHub's Windows runner).
const STATS_TIMEOUT = 60_000;

describe("shuffle", () => {
  it("returns a permutation and leaves the input untouched", () => {
    const input = deckIds("all");
    const out = shuffle(input);
    expect(out).toHaveLength(78);
    expect([...out].sort((a, b) => a - b)).toEqual(input);
    expect(input).toEqual(deckIds("all"));
  });

  it("puts every card on top equally often", () => {
    const trials = 78 * 400;
    const counts = new Array(78).fill(0);
    for (let i = 0; i < trials; i++) counts[shuffle(deckIds("all"))[0]]++;
    expect(chiSquare(counts, trials / 78)).toBeLessThan(CHI2_P001[77]);
  }, STATS_TIMEOUT);

  it("moves a given card to every position equally often", () => {
    const trials = 22 * 500;
    const counts = new Array(22).fill(0);
    for (let i = 0; i < trials; i++) counts[shuffle(deckIds("major")).indexOf(0)]++;
    expect(chiSquare(counts, trials / 22)).toBeLessThan(CHI2_P001[21]);
  }, STATS_TIMEOUT);
});

describe("coinFlip / drawCards", () => {
  it("reverses about half of the cards", () => {
    const trials = 20000;
    let reversed = 0;
    for (let i = 0; i < trials; i++) if (coinFlip()) reversed++;
    expect(chiSquare([reversed, trials - reversed], trials / 2)).toBeLessThan(CHI2_P001[1]);
  });

  it("draws distinct cards from the chosen scope", () => {
    const drawn = drawCards(12, "major", true);
    const ids = drawn.map((d) => d.cardId);
    expect(new Set(ids).size).toBe(12);
    expect(ids.every((id) => id >= 0 && id < 22)).toBe(true);
  });

  it("never reverses when reversals are off", () => {
    for (let i = 0; i < 50; i++) {
      expect(drawCards(10, "all", false).every((d) => !d.reversed)).toBe(true);
    }
  });

  it("refuses to draw more cards than the deck holds", () => {
    expect(() => drawCards(23, "major", true)).toThrow(RangeError);
  });
});
