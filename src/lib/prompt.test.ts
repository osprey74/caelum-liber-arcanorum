import { describe, expect, it } from "vitest";
import type { Reading } from "../types/reading";
import { buildCopyText, buildPrompt, SYSTEM_PROMPT } from "./prompt";

const reading: Reading = {
  id: "t",
  createdAt: "2026-10-01T12:00:00Z",
  spreadId: "three",
  question: "新しい仕事に向けて、今の私に必要なことは？",
  settings: { useReversed: true, scope: "all" },
  cards: [
    { cardId: 0, reversed: false },
    { cardId: 13, reversed: true },
    { cardId: 21, reversed: false },
  ],
};

describe("buildPrompt", () => {
  it("lists the spread, every position with its card and orientation, and the question", () => {
    const text = buildPrompt(reading);
    expect(text).toContain("スプレッド：");
    expect(text.match(/^\d+\. /gm)).toHaveLength(3);
    expect(text).toContain("（逆位置）");
    expect(text).toContain("キーワード：");
    expect(text).toContain("新しい仕事に向けて");
  });

  it("marks an empty question", () => {
    expect(buildPrompt({ ...reading, question: "  " })).toMatch(/# 問い\n（なし）\n/);
  });

  it("asks for the overall length of the spread", () => {
    expect(buildPrompt(reading)).toMatch(/全体の読み解き：800〜1200字$/);
    expect(buildPrompt({ ...reading, spreadId: "one", cards: reading.cards.slice(0, 1) })).toMatch(/600〜900字$/);
  });
});

describe("buildCopyText", () => {
  it("contains the system prompt and the reading", () => {
    const text = buildCopyText(reading);
    expect(text).toContain(SYSTEM_PROMPT.trim().slice(0, 40));
    expect(text).toContain(buildPrompt(reading));
  });
});
