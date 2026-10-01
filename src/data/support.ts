// Text of the support screen (shown instead of a reading when a question shows serious distress) and of the
// safety notice (violence, threats or stalking: shown before the reading). Numbers and hours were checked on
// 2026-10-01; check them again on the official pages below before publishing (see README).
//   厚生労働省「まもろうよ こころ」 https://www.mhlw.go.jp/mamorouyokokoro/
//   警察庁 警察相談専用電話 https://www.npa.go.jp/bureau/soumu/soudan/soudanmadoguti.pdf
//   内閣府 DV相談ナビ https://www.gender.go.jp/policy/no_violence/e-vaw/soudankikan/01.html

export interface SupportLine {
  name: string;
  detail: string;
  /** Phone number or URL. */
  contact: string;
}

export const SUPPORT_LEAD = [
  "もし今、つらいお気持ちを抱えていらっしゃるなら、この画面では占いをお休みして、まずはご自身の心と体を大切にしてください。一人で抱えず、話を聞いてくれる窓口を頼ってください。",
];

export const SUPPORT_LINES: SupportLine[] = [
  { name: "#いのちSOS", detail: "毎日24時間・無料", contact: "0120-061-338" },
  { name: "よりそいホットライン", detail: "24時間・無料", contact: "0120-279-338" },
  { name: "いのちの電話", detail: "無料・毎日16時〜21時", contact: "0120-783-556" },
  { name: "こころの健康相談統一ダイヤル", detail: "受付時間は地域により異なります", contact: "0570-064-556" },
  {
    name: "厚生労働省「まもろうよ こころ」",
    detail: "電話・SNSの相談窓口の一覧",
    contact: "https://www.mhlw.go.jp/mamorouyokokoro/",
  },
];

export const SUPPORT_EMERGENCY = "命に関わる緊急のときは、119番に連絡してください。";

/** Shown above the reading when the question mentions violence, threats or stalking. */
export const SAFETY_LEAD =
  "暴力や脅し、付きまといなどでお困りのときは、占いの結果より先に、まずは相談窓口にご相談ください。";

export const SAFETY_LINES: SupportLine[] = [
  {
    name: "警察相談専用電話",
    detail: "ストーカーやDVなど、警察への相談。お住まいの地域の警察の相談窓口につながります",
    contact: "#9110",
  },
  { name: "DV相談ナビ", detail: "お近くの配偶者暴力相談支援センターにつながります", contact: "#8008" },
];

export const SAFETY_EMERGENCY = "身の危険を感じる緊急のときは、110番に連絡してください。";
