import { CARDS, plateName } from "../data/cards";
import SYSTEM_PROMPT from "../data/interpret-system.md?raw";
import { meaningOf, spreadOf } from "../data/readings";
import type { Reading, Spread } from "../types/reading";

export { SYSTEM_PROMPT };

/** Length of the overall reading (「全体の読み解き」) in characters, by spread. */
export const OVERALL_LENGTH: Record<Spread["id"], [number, number]> = {
  one: [600, 900],
  three: [800, 1200],
  celtic: [1200, 1800],
  horoscope: [1200, 1800],
};

/** The user message for the API: the spread, each position with its card, and the question (handoff §5.2). */
export function buildPrompt(reading: Reading): string {
  const spread = spreadOf(reading.spreadId);
  const lines = [
    `スプレッド：${spread.name}（${spread.positions.length}枚）`,
    `山札：${reading.settings.scope === "major" ? "大アルカナのみ（22枚）" : "78枚すべて"}${
      reading.settings.useReversed ? "" : "・逆位置は使わない"
    }`,
    "",
    "# 出たカード",
  ];
  spread.positions.forEach((p, i) => {
    const drawn = reading.cards[i];
    const m = meaningOf(drawn.cardId);
    const keywords = drawn.reversed ? m.keywords_reversed : m.keywords_upright;
    const meaning = p.meaning === p.label ? p.label : `${p.label}（${p.meaning}）`;
    lines.push(
      `${p.index}. ${meaning}：${plateName(CARDS[drawn.cardId])}（${drawn.reversed ? "逆位置" : "正位置"}）`,
      `   キーワード：${keywords.join("、")}`,
    );
  });
  const [min, max] = OVERALL_LENGTH[spread.id];
  lines.push("", "# 問い", reading.question.trim() || "（なし）", "", "# 文章の長さ", `全体の読み解き：${min}〜${max}字`);
  return lines.join("\n");
}

/** Both prompts in one text, to paste into another AI (no API key needed). */
export function buildCopyText(reading: Reading): string {
  return [
    "以下の「指示」に従って、「占いの結果」を読み解いてください。",
    "",
    "===== 指示 =====",
    SYSTEM_PROMPT.trim(),
    "",
    "===== 占いの結果 =====",
    buildPrompt(reading),
  ].join("\n");
}
