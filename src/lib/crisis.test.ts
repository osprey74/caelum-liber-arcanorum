import { describe, expect, it } from "vitest";
import { CARDS, plateName } from "../data/cards";
import { meaningOf } from "../data/readings";
import { needsSafetyNotice, needsSupport, normalize } from "./crisis";

// Questions that must open the support screen.
const DETECT = [
  "死にたい",
  "もう死にたいです。これからどうなりますか",
  "しにたい",
  "シニタイ",
  "死 に た い",
  "消えたい気持ちが止まりません",
  "いなくなりたい",
  "生きていたくない",
  "生きる意味がない気がする",
  "生きるのがつらい",
  "死んだほうがましだと思う",
  "死ぬしかないのかな",
  "自殺を考えています",
  "自傷がやめられない",
  "自分を傷つけてしまう",
  "リスカしてしまった",
  "リストカットの跡を隠したい",
  "首を吊ろうか迷っている",
  "飛び降りたい",
  "電車に飛び込みそうになる",
  "命を絶つべきか",
  "人生を終わりにしたい",
  "オーバードーズしてしまった",
  "遺書を書きました",
  "あいつを殺したい",
  "I want to die",
  "thinking about suicide",
];

// Questions and words that must NOT open it: card names, card meanings and everyday worries.
const PASS = [
  "",
  "死神のカードが出たのですが、どういう意味ですか",
  "吊るされた男の逆位置について",
  "塔が出てこわい",
  "ソードの10は悪い意味ですか",
  "死と再生のテーマについて",
  "仕事を辞めたい",
  "彼と別れたい",
  "疲れた。休むべき？",
  "学校にいきたくない",
  "会社に行きたくない日が続く",
  "死ぬほど忙しい毎日です",
  "死ぬまでに行きたい場所は？",
  "祖父が亡くなって寂しい",
  "ペットが死んでしまって悲しい",
  "新しい世界に飛び込みたい",
  "飛び込み営業はうまくいく？",
  "清水の舞台から飛び降りるつもりで告白したい",
  "人の問題に首を突っ込むべき？",
  "首をつっこみすぎる癖",
  "命をたいせつにしたい",
  "生きる意味を見つけたい",
  "今の転職は自殺行為ですか",
  "わたしにたいして彼はどう思っている？",
  "むしにたいさくをしたい",
  "この関係を終わりにしたい",
  "遺言書の準備について",
  "消したい過去がある",
  "存在感を消したい",
  "DVDを買うべき？",
];

describe("needsSupport", () => {
  it.each(DETECT)("detects: %s", (q) => expect(needsSupport(q)).toBe(true));
  it.each(PASS)("passes: %s", (q) => expect(needsSupport(q)).toBe(false));

  it("never fires on card names or the card meaning texts", () => {
    for (const card of Object.values(CARDS)) {
      expect(needsSupport(plateName(card)), plateName(card)).toBe(false);
      const m = meaningOf(card.id);
      for (const text of [m.upright, m.reversed, m.description, ...m.keywords_upright, ...m.keywords_reversed]) {
        expect(needsSupport(text), `${card.id}: ${text}`).toBe(false);
      }
    }
  });
});

// Questions that must show the safety notice (police / DV lines) before the reading.
const SAFETY = [
  "親から虐待を受けています",
  "夫に暴力を振るわれています",
  "彼に殴られた",
  "彼氏に叩かれることがある",
  "元彼に付きまとわれています",
  "元カレにつきまとわれて怖い",
  "ストーカー被害にあっています",
  "別れ話をしたら脅されました",
  "DVを受けているかもしれない",
  "パートナーのモラハラがつらい",
  "家の前で待ち伏せされる",
];

// Relationship and everyday questions that must not show it.
const NOT_SAFETY = [
  "彼と付き合うべき？",
  "彼につきあってほしいと言われた",
  "DVDを買うべき？",
  "ライバルは脅威になる？",
  "彼との関係はこれからどうなりますか",
  "上司とうまくいかない",
  "結婚を迷っています",
  "後をついていきたい先輩がいる",
];

describe("needsSafetyNotice", () => {
  it.each(SAFETY)("detects: %s", (q) => expect(needsSafetyNotice(q)).toBe(true));
  it.each(NOT_SAFETY)("passes: %s", (q) => expect(needsSafetyNotice(q)).toBe(false));
  it.each(PASS)("passes the everyday questions too: %s", (q) => expect(needsSafetyNotice(q)).toBe(false));

  it("these questions do not open the support screen (the reading goes on)", () => {
    for (const q of SAFETY) expect(needsSupport(q), q).toBe(false);
  });

  it("never fires on the card meaning texts", () => {
    for (const card of Object.values(CARDS)) {
      const m = meaningOf(card.id);
      for (const text of [m.upright, m.reversed, m.description, ...m.keywords_upright, ...m.keywords_reversed]) {
        expect(needsSafetyNotice(text), `${card.id}: ${text}`).toBe(false);
      }
    }
  });
});

describe("normalize", () => {
  it("folds width, case, katakana and spaces", () => {
    expect(normalize("ＳＵＩＣＩＤＥ")).toBe("suicide");
    expect(normalize("シ ニ タ イ")).toBe("しにたい");
  });
});
