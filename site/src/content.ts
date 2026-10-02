// Text of the introduction site, in Japanese and English. Facts here must match the app (README.md, release notes).

export const VERSION = "1.0.0";
export const SIZE_MB = 46;
export const REPO = "https://github.com/osprey74/caelum-liber-arcanorum";
export const DOWNLOAD = `${REPO}/releases/download/v${VERSION}/Liber.Arcanorum_${VERSION}_x64-setup.exe`;
export const RELEASE = `${REPO}/releases/tag/v${VERSION}`;
export const LIBER_CAELI = "https://portfolio.osprey74.com/apps/liber-caeli";
export const PORTFOLIO = "https://portfolio.osprey74.com";

export type Lang = "ja" | "en";

interface Feature {
  title: string;
  body: string;
}

interface Shot {
  src: string;
  alt: string;
  caption: string;
}

interface Faq {
  q: string;
  a: string;
}

export interface Content {
  lang: Lang;
  path: string;
  other: { lang: Lang; path: string; label: string };
  title: string;
  description: string;
  nav: { features: string; screens: string; ai: string; download: string; faq: string };
  hero: { subtitle: string; lead: string; cta: string; meta: string; notes: string };
  intro: { heading: string; body: string[] };
  features: { heading: string; items: Feature[] };
  screens: { heading: string; items: Shot[] };
  cards: { heading: string; body: string };
  ai: { heading: string; body: string[]; points: Feature[]; cost: string };
  care: { heading: string; body: string[] };
  download: {
    heading: string;
    requirements: string;
    steps: string[];
    smartscreen: string;
    cta: string;
    release: string;
    mac: string;
  };
  faq: { heading: string; items: Faq[] };
  footer: { series: string; caeli: string; source: string; credits: string; disclaimer: string };
}

const ja: Content = {
  lang: "ja",
  path: "/",
  other: { lang: "en", path: "/en/", label: "English" },
  title: "Liber Arcanorum — 秘儀の書｜タロット占いアプリ",
  description:
    "オリジナルの絵柄で描いた78枚のタロットで、静かに自分と向き合う Windows 向けのタロット占いアプリ。4種類のスプレッド、カードの意味、Claude による AI 解釈（任意）に対応。無料。",
  nav: { features: "機能", screens: "画面", ai: "AI解釈", download: "ダウンロード", faq: "よくある質問" },
  hero: {
    subtitle: "秘儀の書",
    lead: "オリジナルの絵柄で描いた78枚のタロットで、\n静かに自分と向き合うための一冊を。",
    cta: "Windows 版をダウンロード",
    meta: `v${VERSION} ・ 無料 ・ 約${SIZE_MB}MB`,
    notes: "Windows 10 / 11（64ビット）",
  },
  intro: {
    heading: "カードを引く、ひとときのために",
    body: [
      "Liber Arcanorum（リベル・アルカノールム）は、ラテン語で「秘儀の書」。西洋占星術アプリ Liber Caeli と同じ Caelum シリーズの、タロット占いアプリです。",
      "山札をシャッフルし、カードを一枚ずつめくる。その手ざわりを大切にしながら、カードの意味と、必要なときには AI の読み解きを添えて、問いと向き合う時間をつくります。",
    ],
  },
  features: {
    heading: "機能",
    items: [
      { title: "オリジナルの78枚", body: "大アルカナ22枚と小アルカナ56枚を、このアプリのために制作しました。正位置・逆位置に対応しています。" },
      { title: "4種類のスプレッド", body: "ワンオラクル、スリーカード、ケルト十字、ホロスコープ。問いに合わせて、カードの並べ方を選べます。" },
      { title: "カードの意味", body: "78枚それぞれの正位置・逆位置の意味とキーワードを収録。インターネットにつながっていなくても読めます。" },
      { title: "AI による解釈（任意）", body: "Anthropic の APIキーを登録すると、Claude が引いたカードをもとにリーディングの文章を書きます。" },
      { title: "履歴", body: "占いの結果と解釈は、PC の中に保存されます。あとから読み返して、変化を振り返れます。" },
      { title: "シャッフルとめくりの演出", body: "山札を切る動きと、カードをめくる音。効果音はオフにもできます。" },
    ],
  },
  screens: {
    heading: "画面",
    items: [
      { src: "/images/home.webp", alt: "ホーム画面。左に問いの入力欄と設定、右に4種類のスプレッドの選択肢", caption: "問いを思い描き、スプレッドを選ぶ" },
      { src: "/images/reading-ai.webp", alt: "スリーカードの結果画面。左に3枚のカード、右に AI による解釈の文章", caption: "カードと読み解きを並べて読む" },
      { src: "/images/celtic.webp", alt: "ケルト十字の結果画面。10枚のカードと、カードの意味の一覧", caption: "ケルト十字の10枚と、カードの意味" },
    ],
  },
  cards: {
    heading: "78枚のカード",
    body: "アール・ヌーヴォーの装飾と百合の縁取りで統一した、このアプリだけのデッキです。カード上部のメダリオンには、天体・星座・元素の記号を描いています。",
  },
  ai: {
    heading: "AI による解釈",
    body: [
      "Anthropic の Claude が、スプレッドの位置の意味、出たカードと正逆、あなたの問いをもとに、全体の流れとカードごとの読み解き、これからのヒントを書きます。",
      "使うかどうかは自由です。AI を使わなくても、カードの意味だけで占いを楽しめます。",
    ],
    points: [
      { title: "APIキーはご自身のもの", body: "Anthropic の Console で発行した APIキーを登録して使います。キーは Windows の資格情報マネージャーに保存され、画面やファイルには残りません。" },
      { title: "送るのは、占いの内容だけ", body: "「AIで解釈する」を押したときに、スプレッド・カード・問いを Anthropic に送ります。それ以外の情報は送りません。" },
      { title: "キーがなくても", body: "「プロンプトをコピー」で、同じ指示文をほかの AI に貼り付けて使えます。" },
    ],
    cost: "API の料金はご自身の負担です。目安は、Claude Sonnet 5.5 で1回あたり約2〜4円（2026年10月の実測、スプレッドと文章の長さで変わります）。",
  },
  care: {
    heading: "ご利用にあたって",
    body: [
      "タロット占いは、娯楽と内省のための読み物です。結果は未来を断定するものではありません。健康・お金・法律などの大切な判断は、専門家にご相談ください。",
      "問いに深刻な悩みが読み取れるときは、占いの代わりに相談窓口をご案内します。",
    ],
  },
  download: {
    heading: "ダウンロード",
    requirements: "Windows 10 / 11（64ビット）。管理者権限は不要です。",
    steps: [
      "下のボタンからインストーラーをダウンロードします。",
      "ダウンロードした Liber.Arcanorum_x64-setup.exe を開き、画面の案内に沿ってインストールします。",
      "スタートメニューの「Liber Arcanorum」から起動します。",
    ],
    smartscreen:
      "インストーラーには電子署名がないため、初回は「Windows によって PC が保護されました」と表示されることがあります。その場合は「詳細情報」を押し、「実行」を選んでください。",
    cta: "インストーラーをダウンロード",
    release: "リリースノート（GitHub）",
    mac: "現在、Windows 版のみの提供です。",
  },
  faq: {
    heading: "よくある質問",
    items: [
      { q: "無料ですか？", a: "アプリは無料です。AI による解釈を使う場合のみ、Anthropic の API の料金がご自身にかかります。" },
      { q: "占いの履歴はどこに保存されますか？", a: "お使いの PC の中だけに保存されます。アプリが外部に送ることはありません。" },
      { q: "インターネットにつながっていなくても使えますか？", a: "はい。カードを引くこと、カードの意味を読むこと、履歴を見ることは、オフラインでもできます。AI による解釈だけはインターネット接続が必要です。" },
      { q: "どのモデルを使いますか？", a: "初期設定は Claude Sonnet 5.5 です。設定で Claude Opus 5.5 に切り替えられます。" },
      { q: "アンインストールするには？", a: "Windows の「設定」→「アプリ」→「インストールされているアプリ」から Liber Arcanorum を選び、アンインストールします。" },
    ],
  },
  footer: {
    series: "Caelum シリーズ",
    caeli: "Liber Caeli（西洋占星術）",
    source: "ソースコード（GitHub）",
    credits: "カード名には Shippori Mincho（SIL Open Font License 1.1）を使用しています。",
    disclaimer: "占いは娯楽を目的としたものです。",
  },
};

const en: Content = {
  lang: "en",
  path: "/en/",
  other: { lang: "ja", path: "/", label: "日本語" },
  title: "Liber Arcanorum — Book of the Arcana | Tarot reading app",
  description:
    "A tarot reading app for Windows with 78 cards of original art. Four spreads, card meanings and optional AI interpretations by Claude. Free.",
  nav: { features: "Features", screens: "Screens", ai: "AI reading", download: "Download", faq: "FAQ" },
  hero: {
    subtitle: "Book of the Arcana",
    lead: "Seventy-eight cards of original art,\nfor a quiet hour with your own question.",
    cta: "Download for Windows",
    meta: `v${VERSION} · Free · ${SIZE_MB} MB`,
    notes: "Windows 10 / 11 (64-bit)",
  },
  intro: {
    heading: "For the moment you draw a card",
    body: [
      "Liber Arcanorum is Latin for “Book of the Arcana”. It is a tarot reading app of the Caelum series, sister to the astrology app Liber Caeli.",
      "Shuffle the deck and turn the cards one by one. The app keeps that feel, and adds the meaning of each card and, when you want it, a reading written by AI.",
    ],
  },
  features: {
    heading: "Features",
    items: [
      { title: "78 original cards", body: "All 22 Major and 56 Minor Arcana were made for this app, upright and reversed." },
      { title: "Four spreads", body: "One Card, Three Cards, Celtic Cross and Horoscope: choose the layout for your question." },
      { title: "Card meanings", body: "Upright and reversed meanings and keywords for all 78 cards, available offline. (In Japanese.)" },
      { title: "AI reading (optional)", body: "With your Anthropic API key, Claude writes a reading of the cards you drew." },
      { title: "History", body: "Readings and interpretations stay on your PC, to read again later." },
      { title: "Shuffle and turn", body: "The deck shuffles and each card turns with a soft sound. Sound effects can be turned off." },
    ],
  },
  screens: {
    heading: "Screens",
    items: [
      { src: "/images/home.webp", alt: "Home screen with the question field and settings on the left and the four spreads on the right", caption: "Hold a question and choose a spread" },
      { src: "/images/reading-ai.webp", alt: "Three Cards reading with the cards on the left and the AI interpretation on the right", caption: "The cards and their reading side by side" },
      { src: "/images/celtic.webp", alt: "Celtic Cross reading with ten cards and the list of card meanings", caption: "The ten cards of the Celtic Cross and their meanings" },
    ],
  },
  cards: {
    heading: "The 78 cards",
    body: "A deck of its own, unified by Art Nouveau ornament and a border of lilies. The medallion at the top carries a planet, sign or element symbol.",
  },
  ai: {
    heading: "AI reading",
    body: [
      "Anthropic’s Claude reads the meaning of each position, the cards and their orientation, and your question, then writes the overall flow, a note for each card and hints for what comes next.",
      "It is entirely optional: the card meanings alone are enough for a reading. Readings are written in Japanese.",
    ],
    points: [
      { title: "Your own API key", body: "Register a key issued in the Anthropic Console. It is kept in the Windows Credential Manager and never shown on screen or written to a file." },
      { title: "Only the reading is sent", body: "When you press the AI button, the spread, the cards and your question go to Anthropic. Nothing else is sent." },
      { title: "No key? Copy the prompt", body: "“Copy prompt” gives you the same instructions to paste into another AI." },
    ],
    cost: "API usage is billed to you. As a guide, one reading with Claude Sonnet 5.5 costs about 2–4 yen (measured in October 2026; it depends on the spread and the length of the text).",
  },
  care: {
    heading: "Please note",
    body: [
      "Tarot reading is for entertainment and reflection; it does not predict the future. For decisions about health, money or the law, please consult a professional.",
      "When a question shows serious distress, the app shows support lines instead of a reading.",
    ],
  },
  download: {
    heading: "Download",
    requirements: "Windows 10 / 11 (64-bit). No administrator rights are needed.",
    steps: [
      "Download the installer with the button below.",
      "Open Liber.Arcanorum_x64-setup.exe and follow the steps on screen.",
      "Start Liber Arcanorum from the Start menu.",
    ],
    smartscreen:
      "The installer is not code-signed, so Windows may say “Windows protected your PC” the first time. Choose “More info” and then “Run anyway”.",
    cta: "Download the installer",
    release: "Release notes (GitHub)",
    mac: "Only a Windows version is available for now.",
  },
  faq: {
    heading: "FAQ",
    items: [
      { q: "Is it free?", a: "The app is free. Only the AI reading uses Anthropic’s API, which is billed to you." },
      { q: "Where is my history kept?", a: "Only on your PC. The app does not send it anywhere." },
      { q: "Does it work offline?", a: "Yes. Drawing cards, reading the card meanings and the history all work offline. Only the AI reading needs an internet connection." },
      { q: "Which model does it use?", a: "Claude Sonnet 5.5 by default; you can switch to Claude Opus 5.5 in the settings." },
      { q: "Is the app in English?", a: "The app and its texts are in Japanese for now." },
      { q: "How do I uninstall it?", a: "In Windows Settings, open Apps › Installed apps, choose Liber Arcanorum and uninstall it." },
    ],
  },
  footer: {
    series: "Caelum series",
    caeli: "Liber Caeli (astrology)",
    source: "Source code (GitHub)",
    credits: "Card names are set in Shippori Mincho (SIL Open Font License 1.1).",
    disclaimer: "Tarot reading is for entertainment.",
  },
};

export const CONTENT: Record<Lang, Content> = { ja, en };
