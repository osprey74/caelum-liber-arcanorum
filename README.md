# Liber Arcanorum

Caelum シリーズのタロット占いアプリです（姉妹アプリ：Liber Caeli）。Tauri v2・React・TypeScript で作っています。

## 開発

```sh
npm install
npm run tauri dev
```

カード絵柄の生成・合成ツールは `tools/tarot-gen/` にあります（`tools/tarot-gen/README.md`）。画像は Git LFS で管理しています。

## 配布と紹介サイト

- **インストーラー**：GitHub Actions（`.github/workflows/release.yml`）で Windows 向けの NSIS インストーラーを作ります。`v1.2.3` の形のタグを push すると下書きのリリースに添付され、手動実行では Artifacts に保存されます。
- **紹介サイト**：`site/`（Astro）。https://arcanorum.osprey74.com に、`.github/workflows/site.yml` が FTP で配置します（`site/**` を main に push したとき）。配置には、リポジトリの Secrets に `ONAMAE_HOST`・`ONAMAE_FTP_USER`・`ONAMAE_FTP_PASSWORD` が必要です。
  - 手元での確認：`cd site && bun install && bun run dev`
  - バージョンを上げたときは、`site/src/content.ts` の `VERSION`（ダウンロードの URL に使います）と `SIZE_MB` も更新します。
  - サイトの画面写真は `site/public/images/` にあります。アプリの画面を変えたときは撮り直します。

## AI による解釈

引いたカードの解釈を、Anthropic の Claude API で生成します。

- APIキーは、アプリの「AIの設定」から登録します。キーは OS の資格情報ストア（Windows の資格情報マネージャー、macOS のキーチェーン）に `com.osprey74.liberarcanorum` として保存され、画面やファイルには残りません。
- モデルの初期値は Claude Sonnet 5.5（`claude-sonnet-5-5`）で、設定画面で Claude Opus 5.5 に切り替えられます。設定ファイル（Windows では `%APPDATA%\liber-arcanorum\config.json`）の `"model"` で、ほかのモデルも指定できます。
- システムプロンプトは `src/data/interpret-system.md` です。
- APIキーがなくても、「プロンプトをコピー」でほかの AI に貼り付けて使えます。カードごとの意味は、オフラインでも読めます。

### 相談窓口の案内

問いに深刻な悩みが読み取れる場合は占いを行わずに相談窓口を、暴力・脅し・付きまといなどが読み取れる場合は解釈の前に警察と DV の相談窓口を案内します。文面は `src/data/support.ts`、判定に使う言葉は `src/lib/crisis.ts`（テストは `src/lib/crisis.test.ts`）にあります。

**公開前に、案内文の電話番号と受付時間を次の公式ページで再確認してください。** 番号や受付時間は変わることがあります（最終確認：2026-10-01）。

- 厚生労働省「まもろうよ こころ」：<https://www.mhlw.go.jp/mamorouyokokoro/>
- 警察庁 警察相談専用電話「#9110」：<https://www.npa.go.jp/bureau/soumu/soudan/soudanmadoguti.pdf>
- 内閣府 男女共同参画局 DV相談ナビ「#8008」：<https://www.gender.go.jp/policy/no_violence/e-vaw/soudankikan/01.html>

システムプロンプト（`src/data/interpret-system.md`）にも #9110・#8008 の文面があります。番号を変えるときは両方を直してください。

## 素材のライセンスと出典

### カード絵柄

78枚のカード絵柄、フレーム、裏面は、このプロジェクトのために作成したものです。

### フォント

カード名のプレート、題字、見出し、主なボタンには **Shippori Mincho SemiBold** を使います（2026-10-01 決定）。AI の解釈やカードの意味などの本文は OS の明朝体（Windows は游明朝、macOS はヒラギノ明朝）、そのほかの文字は OS のゴシック体（Yu Gothic UI、ヒラギノ角ゴ）で表示します（`tailwind.config.js` の `fontFamily`）。SIL Open Font License 1.1（OFL）のもと、アプリに同梱しています（CDN からは読み込みません）。

| 項目 | 内容 |
| --- | --- |
| 書体 | Shippori Mincho SemiBold |
| 著作権者 | Copyright 2021 The Shippori Mincho Project Authors（https://github.com/fontdasu/ShipporiMincho） |
| 出典 | https://github.com/google/fonts/tree/main/ofl/shipporimincho |
| ライセンス | SIL Open Font License 1.1。本文は `src/assets/fonts/ShipporiMincho-OFL.txt`（元の TTF とともに `tools/fonts/` にも同梱） |
| 同梱の形 | 使用する文字だけに絞ったサブセット（WOFF2、約56KB）。`tools/fonts/build_fonts.py` で作成 |

OFL の条件により、サブセットにした書体も同じライセンスで配布しています。

#### サブセットの対象文字

アプリには、次の文字だけに絞った Shippori Mincho を同梱しています（264文字、2026-10-01 時点）。

- `src/data/cards.json` の全カードの日本語名（`name_ja`）、ローマ数字（`roman`）、英語名（`name_en`）に出てくる文字
- `src/data/spreads.json` のスプレッド名と位置の名前に出てくる文字
- ASCII の印字可能な文字
- `tools/fonts/build_fonts.py` の `EXTRA_TEXT`（数字、ローマ数字、「・ー」、「正逆位置表裏面」など）と `DISPLAY_TEXT`（題字・見出し・ボタンの決まった文言）に書いた文字

```text
 !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~　、。「」いえおかきくこごさしすただつてとにのひぶみよらるれをイウエオカキクグケコシジスセソタットドナハヒフプペホメャラリルレロワン・ー世人伝位体儀先全判制力勢十占去吊周命問囲在塔太女姿字定害審履山帝師底心思恋恐悪意愚戦描教星書最月望未本札来果根標正歴死況浮潜状現男界皇目神秘第節終結置義者術表裏解設読識車輪近逆運過釈陽障隠面顕願魔（）：
```

対象文字を追加する手順（意味の文章など、カード名以外にも Shippori Mincho を使う場合）：

1. 追加したい文字を `tools/fonts/build_fonts.py` に加えます。
   - 見出しやボタンに新しい文言を `font-display` で使う場合は、`DISPLAY_TEXT` に書き足します。
   - 意味の文章（`src/data/meanings.json` など）を丸ごと対象にする場合は、`charset()` でそのファイルの文字列も読み込むようにします。
2. `py -3.11 tools/fonts/build_fonts.py` を実行し、`src/assets/fonts/shippori-mincho-semibold.woff2` を作り直します。
3. 表示に使う文字がすべて含まれているかを、ギャラリー画面などで確認します。含まれない文字は別の書体（システムの明朝体）で表示されるため、見た目が混ざります。
4. 作り直した WOFF2 をコミットします（元の TTF は `tools/fonts/` に Git LFS で保存しています）。

文章全体を対象にすると、ファイルが大きくなります（常用漢字を含めると数百KB〜1MB程度）。その場合は、本文だけ別のシステム書体にする方法も検討してください。

### 記号の SVG

メダリオンの天体7種・星座12種・元素4種の記号は、このプロジェクトで描いたオリジナルの SVG パスです（`src/components/Glyph.tsx`）。フォントの文字は使っていません。
