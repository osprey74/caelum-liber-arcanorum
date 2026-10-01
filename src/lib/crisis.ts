// Two checks on the question, run before anything is drawn or sent:
// - needsSupport: serious distress (suicide, self-harm, a wish to kill). The question is not read with the
//   cards; the app shows the support screen instead (handoff §5.3). The system prompt asks the model for the
//   same as a second layer ([[SUPPORT]]).
// - needsSafetyNotice: violence, threats, stalking or abuse. The reading goes on, but the police and DV
//   consultation lines are shown first (the system prompt asks the model to open with them too).
//
// The terms are written for the normalized text (see normalize): NFKC, lower case, katakana as hiragana,
// no spaces. They are phrases, not single words, so card names (死神, 吊るされた男, 塔) and everyday
// questions (仕事を辞めたい, 新しい世界に飛び込みたい, 死ぬほど忙しい) do not match. See crisis.test.ts.

/** Phrases that show suicidal thoughts or self-harm. */
export const SELF_HARM_TERMS: readonly RegExp[] = [
  // hiragana form: "わたしにたいして" (私に対して), "むしにたいさく" (虫に対策) must not match
  /死にたい|しにたい(?!して|する|さく|へん)/,
  /死のう|死んでしまいたい|死んで楽に|死ぬしかない|死ぬつもり|死ぬ方法|死ねたら|死なせて/,
  /死んだ(方|ほう)が(まし|楽|いい)/,
  /消えたい|きえたい|消えてしまいたい|消えてなくなりたい|いなくなりたい/,
  // kanji only: "学校にいきたくない" (行きたくない) must not match
  /生きていたくない|生きたくない|いきていたくない/,
  /生きる(の|こと)が(つらい|辛い|しんどい)|生きていくのが(つらい|辛い|しんどい)/,
  /(生きる|生きている|生きてる)意味が(ない|無い)/,
  /自殺(?!行為)|自死|自傷|自分を傷つけ/,
  /りすとかっと|りすか(?!ー)/,
  // "首を突っ込む" (首をつっこむ) must not match
  /首を(吊|つ)(る|ろう|って|りたい)|首吊|首つり/,
  // "清水の舞台から飛び降りる" is an idiom for a bold decision
  /(?<!舞台から)飛び降り(たい|よう|て死|自殺)/,
  /(電車|線路|ほーむ)に飛び込/,
  // "命をたいせつに" must not match
  /命を(絶|断)|命をた(つ|ち|と)|自ら命|人生を終わ(り|ら)に?(したい|せたい|せる)/,
  /おーばーどーず|過量服薬|大量服薬|薬を大量に/,
  /遺書/,
  /suicid|killmyself|wanttodie|self-?harm/, // spaces are removed by normalize
];

/** A wish to kill or be killed: also the support screen. */
export const HARM_TERMS: readonly RegExp[] = [/殺したい|殺してほしい|殺して欲しい/];

/** Phrases that show violence, threats, stalking or abuse: the safety notice comes before the reading. */
export const SAFETY_TERMS: readonly RegExp[] = [
  /虐待/,
  /暴力|暴行|殴られ|殴ってく|蹴られ|叩かれ/,
  /(?<![a-z])dv(?![a-z])|でぃーぶい|もらはら/, // "dvd" must not match
  // "脅威" must not match
  /脅され|脅して|脅迫|脅しを/,
  // "付き合う" must not match
  /付きまと|つきまと|すとーかー|待ち伏せ|後をつけ(られ|て来)/,
  /監禁/, // not "閉じ込められた気持ち" (the Eight of Swords meaning)
];

/** NFKC, lower case, katakana → hiragana, without spaces. */
export function normalize(text: string): string {
  return text
    .normalize("NFKC")
    .toLowerCase()
    .replace(/[ァ-ヶ]/g, (c) => String.fromCharCode(c.charCodeAt(0) - 0x60))
    .replace(/\s+/g, "");
}

/** True when the question should open the support screen instead of a reading. */
export function needsSupport(question: string): boolean {
  const text = normalize(question);
  if (!text) return false;
  return [...SELF_HARM_TERMS, ...HARM_TERMS].some((re) => re.test(text));
}

/** True when the reading should start with the police and DV consultation lines. */
export function needsSafetyNotice(question: string): boolean {
  const text = normalize(question);
  return text !== "" && SAFETY_TERMS.some((re) => re.test(text));
}

/** The model's reply when it found serious distress itself (see src/data/interpret-system.md). */
export const SUPPORT_MARKER = "[[SUPPORT]]";
