// Cryptographically secure randomness for shuffling (Web Crypto, available in the Tauri webview).

type RandomSource = (buffer: Uint32Array) => Uint32Array;

const cryptoSource: RandomSource = (buffer) => crypto.getRandomValues(buffer);

/**
 * Uniform integer in [0, max) from a 32-bit random source, without modulo bias:
 * values in the incomplete last block are rejected and drawn again.
 */
export function randomInt(max: number, source: RandomSource = cryptoSource): number {
  if (!Number.isInteger(max) || max <= 0 || max > 2 ** 32) {
    throw new RangeError(`randomInt: max must be an integer in 1..2^32, got ${max}`);
  }
  const limit = 2 ** 32 - (2 ** 32 % max); // largest multiple of max that fits
  const buf = new Uint32Array(1);
  for (;;) {
    const v = source(buf)[0];
    if (v < limit) return v % max;
  }
}

/** Fisher–Yates shuffle; returns a new array. */
export function shuffle<T>(items: readonly T[], source: RandomSource = cryptoSource): T[] {
  const a = items.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = randomInt(i + 1, source);
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

/** true with probability 1/2. */
export function coinFlip(source: RandomSource = cryptoSource): boolean {
  return randomInt(2, source) === 1;
}
