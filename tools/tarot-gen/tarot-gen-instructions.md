# タロットカード絵柄 一括生成ツール 指示書（Claude Code 向け）

作成日：2026-09-30
対象：Caelum Liber Arcanorum（Caelum シリーズのタロットアプリ／Caelum Liber Caeli とは別アプリ）用アセット（大アルカナ22枚）

---

## 0. 目的

- 共通フレーム（`frame.png`）の中央アーチ窓に収める**中央絵柄**を、OpenAI 画像APIで一括生成する。
- 1枚につき複数案を生成し、**人が選定**した採用案のみをフレームと**自動合成**する。
- カード名・番号・天体記号は**画像に含めない**。これらはアプリ側（React/SVG）で重ねる。

## 1. 前提確認（実装前に必ず実施し、結果を報告すること）

> **2026-09-30 更新**：総司の判断により、生成の方式を OpenAI API（APIキー認証）から **OpenAI 公式の Codex CLI（ChatGPT サインイン、`codex exec` と標準の `$imagegen`）** に変更した。以下の §1・§3 のうち、APIキー、エンドポイント、品質、概算費用に関する記述は、Codex CLI 方式では「5時間枠消費の目安」の表示などに読み替える。詳細は `README.md` を参照。

1. 使用中の CLI が **OpenAI 公式の CLI / SDK（APIキー認証）** であることを確認する。
   - ChatGPT の Web 画面をブラウザ操作する方式は使用しないこと（利用規約上のリスクがあるため）。
   - 公式でない場合は作業を止め、報告すること。
2. APIキーは環境変数 `OPENAI_API_KEY` から読むこと。コード・ログ・リポジトリにキーを書かないこと。
3. 公式ドキュメント（https://developers.openai.com/api/docs/guides/image-generation ）を確認し、次の2点を報告すること。
   - `gpt-image-2` が **images/edits（参照画像付き生成）** に対応しているか。非対応なら `gpt-image-1.5` を使う。
   - 縦長サイズ `1024x1536`、品質 `medium`、1リクエストあたりの生成枚数 `n` が使えるか。

## 2. ディレクトリ構成

```
tools/tarot-gen/
├── README.md
├── cards.json            # 22枚分のカード定義（§5）
├── style.txt             # 固定スタイルブロック（§4、変更禁止）
├── refs/
│   ├── style_ref.png     # 参照画像（採用済みの「星」の絵柄）
│   └── frame.png         # 共通フレーム
├── generate.py           # 生成スクリプト
├── composite.py          # 合成スクリプト
├── selected.json         # 人が記入する採用案リスト（§7）
└── out/
    ├── raw/              # 生成案（例：17_star_a.png）
    ├── composite/        # 合成済み（例：17_star.png）
    ├── log.jsonl         # 生成ログ
    └── failures.json     # 失敗したカードの一覧
```

`refs/` の画像は総司が配置する。`out/` は `.gitignore` に追加すること。

## 3. 生成仕様（generate.py）

| 項目 | 値 |
|---|---|
| エンドポイント | images/edits（`refs/style_ref.png` を参照画像として添付） |
| モデル | `gpt-image-2`（§1の確認結果により `gpt-image-1.5`） |
| サイズ | `1024x1536` |
| 品質 | `medium`（引数で変更可） |
| 1枚あたりの案数 | 3（`--variants` で変更可） |
| 保存名 | `{id:02d}_{slug}_{a|b|c}.png` |

### 3.1 プロンプトの組み立て

次の順に連結して送信すること。

```
Use the attached image ONLY as a style reference (line, color, texture, level of detail).
Do not copy its composition or subject.

{style.txt の全文}

[CARD]
Title (do not write it): {name_en}
Subject: {subject}
Key symbols: {symbols}
Astrological accent: {astro_accent}, woven subtly into the halo pattern as imagery, not as written symbols.
```

### 3.2 必須機能

- `--dry-run`：API を呼ばず、組み立てたプロンプトと**概算費用**を表示するだけ。
- `--only 0,17,21`：指定したカードのみ生成する。
- 本番実行前に、生成総枚数と概算費用を表示して **y/N の確認**を取ること。
- 既存ファイルは上書きしない。既に存在する案はスキップする（`--force` の指定時のみ上書き）。
- 並列数は最大2。HTTP 429 / 5xx は指数バックオフで最大3回リトライする。
- コンテンツ審査による拒否やエラーがあっても**停止せず**、次のカードへ進むこと。失敗分は `failures.json` に記録する。
- `log.jsonl` に1案ごとに次の項目を記録する：日時、カードID、モデル、品質、プロンプト全文、出力ファイル名、成否。

## 4. style.txt（固定スタイルブロック・変更禁止）

```
[STYLE — FIXED]
Art Nouveau illustration in the manner of Alphonse Mucha.
Elegant flowing contour lines of consistent medium weight; graceful figure with long, stylized swirling hair
and softly draped flowing robes; a large circular halo disc behind the figure decorated with fine geometric
and floral patterns; botanical ornaments (lilies, laurel, vines); flat decorative shading with subtle gradients;
vintage color lithograph texture.
Palette: deep midnight navy, antique gold, muted teal, soft ivory, occasional dusty rose. No neon, no saturated colors.
Composition: vertical 2:3, single central figure, balanced and near-symmetrical, framed by an arch shape,
serene expression, soft glowing light from above.
Keep the main subject in the upper and central area; keep important elements away from the bottom 10%
and the outer 5% on the left and right of the image (the edges will be cropped).
Keep important elements away from the upper-left and upper-right corners; the top of the image will be cropped into a rounded arch.
Keep identical style, line weight, lighting, and level of detail across the whole series.
Exclude: text, letters, numbers, astrological glyphs, captions, card border, frame, watermark, signature,
photorealism, 3D render.
```

## 5. cards.json

`glyph` はアプリ側の重ね描き用のメタデータであり、プロンプトには含めないこと。

> **2026-09-30 更新**：正本は `tools/tarot-gen/cards.json` とする。以下は初版であり、次の方針で改訂済み。
>
> - 人物の性別はライダー・ウェイト・スミス版の伝承どおりに `subject` / `symbols` へ明記する（例：愚者・魔術師・隠者は男性、女教皇・女帝・力・正義・星・世界は女性、節制の天使は Waite の記述に従い両性具有）。
> - 恋人・悪魔・審判は男女（審判は子を含む）、死神は倒れた王・乙女・子・司教、塔は落下する2人の男（1人は王冠）を明記する。
> - 裸体で描かれる伝統図像（恋人・星・太陽・審判など）も、style.txt の「draped robes」に従い着衣で描く。
> - 星は「exactly seven small eight-pointed stars around the large star」を明記する。

```json
[
  {"id":0,"slug":"fool","roman":"0","name_en":"The Fool","name_ja":"愚者","subject":"young traveler stepping toward a cliff edge under an open sky","symbols":"small white dog, bundle on a staff, white rose","astro_accent":"Air, swirling wind and feathers","glyph":"🜁"},
  {"id":1,"slug":"magician","roman":"I","name_en":"The Magician","name_ja":"魔術師","subject":"figure raising a wand skyward with the other hand pointing down","symbols":"table with a cup, a sword, a pentacle and a wand","astro_accent":"Mercury, small wings","glyph":"☿"},
  {"id":2,"slug":"high_priestess","roman":"II","name_en":"The High Priestess","name_ja":"女教皇","subject":"veiled priestess seated between a dark pillar and a light pillar","symbols":"scroll on her lap, veil patterned with pomegranates","astro_accent":"Moon, crescent at her feet","glyph":"☽"},
  {"id":3,"slug":"empress","roman":"III","name_en":"The Empress","name_ja":"女帝","subject":"crowned woman seated in a lush garden beside a flowing stream","symbols":"ripening wheat, soft cushions","astro_accent":"Venus, roses and doves","glyph":"♀"},
  {"id":4,"slug":"emperor","roman":"IV","name_en":"The Emperor","name_ja":"皇帝","subject":"bearded ruler seated on a stone throne with mountains behind","symbols":"orb and scepter","astro_accent":"Aries, ram horns","glyph":"♈"},
  {"id":5,"slug":"hierophant","roman":"V","name_en":"The Hierophant","name_ja":"教皇","subject":"elder in a triple crown raising a hand in blessing","symbols":"two kneeling acolytes, crossed keys","astro_accent":"Taurus, bull motifs","glyph":"♉"},
  {"id":6,"slug":"lovers","roman":"VI","name_en":"The Lovers","name_ja":"恋人","subject":"two figures facing each other beneath a winged angel","symbols":"a fruit tree and a tree of flames","astro_accent":"Gemini, twin symmetry","glyph":"♊"},
  {"id":7,"slug":"chariot","roman":"VII","name_en":"The Chariot","name_ja":"戦車","subject":"armored figure in a star-canopied chariot","symbols":"a dark sphinx and a light sphinx pulling the chariot","astro_accent":"Cancer, shell-like armor","glyph":"♋"},
  {"id":8,"slug":"strength","roman":"VIII","name_en":"Strength","name_ja":"力","subject":"gentle woman calmly closing a lion's jaws","symbols":"flower garland linking the woman and the lion","astro_accent":"Leo, sunburst mane","glyph":"♌"},
  {"id":9,"slug":"hermit","roman":"IX","name_en":"The Hermit","name_ja":"隠者","subject":"cloaked elder standing on a snowy peak","symbols":"lantern containing a six-pointed star, wooden staff","astro_accent":"Virgo, wheat sheaves","glyph":"♍"},
  {"id":10,"slug":"wheel_of_fortune","roman":"X","name_en":"Wheel of Fortune","name_ja":"運命の輪","subject":"great ornate wheel floating in clouds","symbols":"sphinx atop the wheel, serpent descending, four winged creatures","astro_accent":"Jupiter, expansive rays","glyph":"♃"},
  {"id":11,"slug":"justice","roman":"XI","name_en":"Justice","name_ja":"正義","subject":"crowned figure seated between two pillars","symbols":"upright sword and balanced scales","astro_accent":"Libra, balance motifs","glyph":"♎"},
  {"id":12,"slug":"hanged_man","roman":"XII","name_en":"The Hanged Man","name_ja":"吊るされた男","subject":"serene man hanging upside down by one foot from a living tree","symbols":"glowing halo around his head","astro_accent":"Water, gentle ripples","glyph":"🜄"},
  {"id":13,"slug":"death","roman":"XIII","name_en":"Death","name_ja":"死神","subject":"armored skeleton riding a white horse toward a sunrise","symbols":"black banner bearing a white rose, two distant towers","astro_accent":"Scorpio, eagle motif","glyph":"♏"},
  {"id":14,"slug":"temperance","roman":"XIV","name_en":"Temperance","name_ja":"節制","subject":"winged angel pouring water between two cups, one foot on land and one in water","symbols":"irises, a path leading to a rising sun","astro_accent":"Sagittarius, arrow motifs","glyph":"♐"},
  {"id":15,"slug":"devil","roman":"XV","name_en":"The Devil","name_ja":"悪魔","subject":"horned bat-winged figure seated on a dark pedestal","symbols":"two loosely chained figures below","astro_accent":"Capricorn, goat horns","glyph":"♑"},
  {"id":16,"slug":"tower","roman":"XVI","name_en":"The Tower","name_ja":"塔","subject":"tall tower struck by lightning","symbols":"crown blown off the top, flames and falling sparks","astro_accent":"Mars, red-gold fire","glyph":"♂"},
  {"id":17,"slug":"star","roman":"XVII","name_en":"The Star","name_ja":"星","subject":"figure kneeling at a pool's edge, one foot on land and one in water, pouring two jugs, one into the pool and one onto the land","symbols":"exactly seven small eight-pointed stars around one large eight-pointed star, a bird on a distant tree","astro_accent":"Aquarius, flowing water","glyph":"♒"},
  {"id":18,"slug":"moon","roman":"XVIII","name_en":"The Moon","name_ja":"月","subject":"full moon with a serene face above a path between two towers","symbols":"a dog and a wolf howling, a crayfish emerging from a pool","astro_accent":"Pisces, two fish","glyph":"♓"},
  {"id":19,"slug":"sun","roman":"XIX","name_en":"The Sun","name_ja":"太陽","subject":"radiant sun with a serene face above a joyful child on a white horse","symbols":"sunflowers","astro_accent":"Sun, golden rays","glyph":"☉"},
  {"id":20,"slug":"judgement","roman":"XX","name_en":"Judgement","name_ja":"審判","subject":"angel blowing a trumpet from the clouds","symbols":"banner on the trumpet, figures below rising with open arms","astro_accent":"Fire, flames","glyph":"🜂"},
  {"id":21,"slug":"world","roman":"XXI","name_en":"The World","name_ja":"世界","subject":"dancing figure inside an oval laurel wreath","symbols":"two wands, four winged creatures in the corners","astro_accent":"Saturn, rings","glyph":"♄"}
]
```

## 6. 合成仕様（composite.py）

- **窓の検出**：`frame.png` の中心画素 (512, 768) の色を基準に、色差の閾値30以内の連結領域を窓とする。穴埋め後、3px膨張させる。
  - 実測値の目安：x=150〜872、y=247〜1234（約723×988px）。検出結果がこれと大きく異なる場合は警告を出すこと。
- **配置**：絵柄を窓の外接矩形を覆う最小倍率で縮小し、**左右は中央揃え・上端揃え**で切り抜く。
- **マスク**：窓マスクに半径1pxのぼかしをかけ、フレームの上に絵柄を貼り込む。
- **出力**：`out/composite/{id:02d}_{slug}.png`（PNG、1024×1536）。
- **重ねない要素**：カード名・番号・天体記号は画像に重ねない（アプリ側で描画する）。
- **確認用一覧**：`--contact-sheet` 指定時、全生成案を並べた一覧画像を `out/contact_sheet.png` に出力する（選定作業用）。

## 7. 選定フロー

1. `generate.py` を実行する。
2. `--contact-sheet` で一覧画像を作り、総司が確認する。
3. 総司が `selected.json` に採用案を記入する（例：`{"17": "a", "0": "c"}`）。
4. 不採用のカードは `--only` で再生成する。必要なら `cards.json` のモチーフを調整する。
5. `composite.py` は `selected.json` に記載されたカードのみを合成する。

## 8. 完了条件

- [ ] §1の確認結果を報告済みである。
- [ ] `--dry-run` でプロンプトと概算費用が表示される。
- [ ] 「星」1枚のみで本番実行し、生成・ログ・合成が一通り動作する。
- [ ] 22枚の一括実行で、失敗があっても最後まで完走し、`failures.json` が出力される。
- [ ] README に使い方（環境変数、主要コマンド、選定フロー）が記載されている。

## 9. 禁止事項

- APIキーをハードコードすること、ログに出力すること。
- ChatGPT の Web 画面をブラウザ自動操作すること。
- `style.txt` を無断で改変すること（変更案がある場合は提案に留める）。
- 確認なしで22枚×複数案の本番生成を実行すること。
