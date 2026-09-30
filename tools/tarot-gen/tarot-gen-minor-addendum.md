# 追補：小アルカナ56枚の生成（Claude Code 向け）

作成日：2026-09-30
対象：Caelum Liber Arcanorum
前提：`tarot-gen-instructions.md`（大アルカナ版）の仕様・禁止事項をすべて引き継ぐ。

---

## 0. 方針

| 区分 | 枚数 | 生成方式 | `method` |
|---|---|---|---|
| エース | 4 | AI生成（場面画・大アルカナと同じ手順） | `ai` |
| 人物札（ペイジ・ナイト・クイーン・キング） | 16 | AI生成（場面画・大アルカナと同じ手順） | `ai` |
| 数札（2〜10） | 36 | **記号装飾配置**：AI生成した素材をスクリプトで配置 | `layout` |

数札をスクリプトで配置する理由は次の2つ。
- 生成AIは記号の**個数を誤りやすい**。配置をコードで行えば、枚数が常に正確になる。
- 同じスートの素材を使い回すため、36枚の**画風が完全にそろう**。

カード定義は `cards_minor.json`（ID 22〜77）に記載済み。並び順は各スートとも「エース → 2〜10 → ペイジ → ナイト → クイーン → キング」で、スートはワンド → カップ → ソード → ペンタクルの順。

## 1. AI生成（エース・人物札の20枚）

- 大アルカナ版の `generate.py` をそのまま流用し、`cards_minor.json` のうち `method: "ai"` のカードのみを対象とする。
- 参照画像・`style.txt`・プロンプトの組み立て方は、大アルカナ版と同一とする。

## 2. 数札用素材（AI生成、計8点）

### 2.1 スート記号（4点、`assets/symbol_{suit}.png`）

- 背景は透過が望ましい。使用モデルが `background: transparent` に対応しているか公式ドキュメントで確認し、結果を報告すること。
- 非対応の場合は、単色（純緑 #00FF00）の背景で生成し、スクリプトでクロマキー処理して透過させる。

プロンプト：

```
{style.txt の [STYLE — FIXED] ブロックから Composition 行と Keep the main subject 行を除いたもの}

[ASSET]
A single {symbol} drawn as an isolated ornamental object, centered, upright, vertical orientation,
occupying about 80% of the image height, on a plain {transparent | flat pure green #00FF00} background.
No figure, no hand, no scenery, no halo, no shadow on the background.
```

| suit | {symbol} |
|---|---|
| wands | wooden wand with small sprouting leaves and gold fittings |
| cups | ornate golden chalice with Art Nouveau engraving |
| swords | straight double-edged sword with an ornate gold hilt, point up |
| pentacles | round golden disc engraved with a five-pointed star inside a circle, lily ornament on the rim |

### 2.2 スート背景（4点、`assets/bg_{suit}.png`、1024×1536）

```
{style.txt の全文}

[ASSET]
Decorative background panel for the {Suit} suit: large circular halo disc with fine geometric
and floral patterns, symmetrical botanical ornaments ({motif}), night sky in deep navy.
The central area must stay calm and uncluttered (symbols will be placed on top later).
No figure, no objects in the center, no text.
```

| suit | {motif} |
|---|---|
| wands | sunflowers, flames and salamander-like curls |
| cups | water lilies and gentle waves |
| swords | clouds, feathers and butterflies |
| pentacles | grape vines, wheat and roses |

- 素材はいずれも1点につき3案を生成し、人が選定する（大アルカナ版と同じ流れ）。

## 3. 配置スクリプト（layout.py）

- **入力**：`assets/bg_{suit}.png`、`assets/symbol_{suit}.png`、`cards_minor.json`（`method: "layout"` のカード）
- **出力**：`out/raw/{id:02d}_{slug}.png`（1024×1536）。以降は大アルカナと同じく `composite.py` でフレームと合成する。

### 3.1 配置座標

座標は画像全体に対する正規化値 (x, y) で、記号の中心位置を表す。

| 枚数 | 配置 |
|---|---|
| 2 | (.50,.30) (.50,.68) |
| 3 | (.50,.24) (.30,.64) (.70,.64) |
| 4 | (.32,.28) (.68,.28) (.32,.68) (.68,.68) |
| 5 | 4の配置 ＋ (.50,.48) |
| 6 | x=.32/.68 × y=.22/.48/.74 |
| 7 | 6の配置 ＋ (.50,.35) |
| 8 | x=.32/.68 × y=.18/.39/.60/.81 |
| 9 | 8の配置 ＋ (.50,.50) |
| 10 | 8の配置 ＋ (.50,.28) (.50,.71) |

### 3.2 記号の大きさと向き

- **大きさ**（画像の高さに対する記号の高さ）：2〜3枚は 0.26、4〜6枚は 0.20、7〜10枚は 0.15。
- **重なり**：記号同士が重なる場合は自動で5%ずつ縮小し、重ならなくなるまで繰り返す。
- **向き**：ワンドとソードは左右の列を ±12° 傾け、中央列は垂直にしてもよい（装飾性のため）。カップとペンタクルは常に正立とする。
- **影**：記号の下に、ごく薄いドロップシャドウ（不透明度20%以下）を付ける。

### 3.3 切り抜き範囲の制約

- 合成時の切り抜き（下端約8.9%）に掛からないよう、**すべての記号の下端が y=0.89 以内に収まる**ことを検証し、はみ出す場合は警告を出すこと。

## 4. 天体対応（アプリ側の重ね描き用メタデータ）

- 数札の `glyph` は「支配天体＋星座」の2文字（例：ワンドの2 = `♂♈`）。ゴールデン・ドーン体系のデカン対応に基づく。
- エースと人物札の `glyph` はスートの元素記号のみ。人物札の天体対応は体系ごとの差が大きいため、今回は採用しない。

| スート | 2・3・4 | 5・6・7 | 8・9・10 |
|---|---|---|---|
| ワンド | 牡羊座：♂ ☉ ♀ | 獅子座：♄ ♃ ♂ | 射手座：☿ ☽ ♄ |
| カップ | 蟹座：♀ ☿ ☽ | 蠍座：♂ ☉ ♀ | 魚座：♄ ♃ ♂ |
| ソード | 天秤座：☽ ♄ ♃ | 水瓶座：♀ ☿ ☽ | 双子座：♃ ♂ ☉ |
| ペンタクル | 山羊座：♃ ♂ ☉ | 牡牛座：☿ ☽ ♄ | 乙女座：☉ ♀ ☿ |

- 上部メダリオンは、2文字が収まるようアプリ側でフォントサイズを自動調整すること。

## 5. 費用見積り（`--dry-run` で必ず再計算・表示すること）

- AI生成：20枚×3案 ＋ 素材8点×3案 ＝ 84枚
- 概算：84枚 × 約0.041ドル ≒ 3.4ドル（gpt-image-2・中品質・縦長の場合）
- 数札36枚は配置処理のみのため、API費用はかからない。

## 6. 完了条件

- [ ] 素材8点の生成と、透過対応状況の報告
- [ ] `layout.py` で36枚を出力し、各カードの記号の個数が枚数と一致すること（自動テストで検証）
- [ ] コンタクトシートを、スート別に4枚（各14枚）で出力する
- [ ] 全56枚が `composite.py` でフレームと合成できること
