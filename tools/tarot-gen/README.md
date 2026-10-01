# tarot-gen

Caelum Liber Arcanorum の大アルカナ22枚の中央絵柄を生成し、共通フレームと合成するツールです。

画像生成には OpenAI 公式の **Codex CLI** の標準画像生成機能（`$imagegen` / gpt-image-2）を使います。ChatGPT アカウントでサインインして使うため、`OPENAI_API_KEY` は不要で、読み込みもしません。

## 必要なもの

- Codex CLI（`npm i -g @openai/codex`）。ChatGPT の有料プラン（Plus / Team など）でサインイン済みであること
  - 確認コマンド：`codex login status` → `Logged in using ChatGPT`
- Python 3.11 以上と、Pillow・numpy・opencv-python

```sh
pip install pillow numpy opencv-python
```

## ファイル構成

| パス | 内容 |
| --- | --- |
| `cards.json` | 22枚のカード定義（正本）。人物の性別はライダー・ウェイト・スミス版の伝承に従う |
| `style.txt` | 固定のスタイル指定（変更する場合は事前に合意すること） |
| `refs/style_ref.png` | 画風の参照画像 |
| `refs/frame.png` | 共通フレーム |
| `refs/backimage.png` | カード裏面 |
| `refs/sword_rough.png` | ソード数札の配置のラフ（1〜10） |
| `cards_minor.json` | 小アルカナ56枚のカード定義 |
| `style_asset.txt` | 数札用素材のスタイル指定（style.txt から人物・光輪・構図の行を除いたもの） |
| `selected.json` | 採用案のリスト（手で記入する。数札は `layout.py` が自動で記入） |
| `selected_assets.json` | 数札用素材の採用案 |
| `layout_config.json` | 数札の配置の設定（光背の円の計測値、ソードの許容リストなど） |
| `swords_traced.json` | ラフからトレースしたソードの剣の座標 |
| `assets/` | 数札用の素材（スート記号・背景・花飾りなど） |
| `designs/` | 総司が手でデザインしたワンド・ソードの数札（記号だけの透過 PNG、2〜10） |
| `out/raw/` | 生成案（`{id:02d}_{slug}_{a,b,c}.png`） |
| `out/composite/` | 合成済みのカード（`{id:02d}_{slug}.png`） |
| `out/log.jsonl` | 1案ごとの生成ログ |
| `out/failures.json` | 直近の実行で失敗した案 |

`out/` は Git の管理対象外です。

## 生成（generate.py）

```sh
python generate.py --dry-run --variants 2            # プロンプトと枠消費の目安を表示するだけ
python generate.py --variants 2 --exclude 17         # 17（星）以外を2案ずつ生成する
python generate.py --only 0,17,21 --variants 3       # 指定したカードだけ生成する
python generate.py --variants 2 --max-images 20      # この実行では最大20枚まで生成する
```

| オプション | 内容 |
| --- | --- |
| `--dry-run` | Codex を呼ばず、プロンプトと枠消費の目安だけを表示する |
| `--only` / `--exclude` | 対象にする／除外するカードID（カンマ区切り） |
| `--variants N` | 1枚あたりの案数（既定3） |
| `--max-images N` | 1回の実行で生成する最大枚数 |
| `--parallel N` | 並列数（1〜2、既定1） |
| `--force` | 既存の案を上書きして再生成する |
| `--yes` | 実行前の確認（y/N）を省略する |
| `--quota-per-image` | 5時間枠に対する1枚あたり消費%の目安（既定0.9） |

- 生成の順番は、全カードの a 案 → b 案 → c 案です。途中で止まっても、全カードに最低1案は揃います。
- 既に存在する案は飛ばします。枠がリセットされたあとに同じコマンドを実行すれば、続きから生成できます。
- 失敗やコンテンツ審査による拒否があっても止まらず、次の案へ進みます。失敗した案は `out/failures.json` に記録されます。
- 一時的なエラーは、待ち時間を延ばしながら最大3回まで再試行します。利用上限を検出した場合は、残りの案を実行せずに終了します。
- 1枚あたり約2〜3分かかります。

### 利用枠の目安（2026-09-30 に ChatGPT Team で実測）

10枚を連続で生成したときの実測値です。

- 5時間枠：1枚あたり約0.9%。1回の枠で作れるのは100枚程度が目安です。
- 週の枠：1枚あたり約0.1%。
- 表示は整数の%なので、どちらの値にも誤差があります。大量に生成する前に、Codex の使用量画面で残量を確認してください。

### 注意

- Codex へのプロンプトで「モデル名」「品質」などの API 用パラメータを指定すると、Codex が API キー方式に切り替わって失敗します。`generate.py` はそのような指定をしないよう組んであります。
- 品質は Codex 標準の設定になり、指定はできません。サイズは 1024×1536 で出力されることを確認済みです。

## 選定と合成（composite.py）

1. `python generate.py ...` で案を生成します。
2. `python composite.py --contact-sheet --no-composite` で一覧画像 `out/contact_sheet.png` を作り、案を見比べます。
3. `selected.json` に採用案を記入します。例：`{"0": "b", "17": "a"}`
4. 不採用のカードは `--only` で再生成します。必要に応じて `cards.json` のモチーフを調整します。
5. `python composite.py` を実行すると、`selected.json` に記入したカードだけを合成します。
6. `python composite.py --contact-sheet --final --no-composite` を実行すると、決定稿だけを並べた一覧画像を `out/contact_sheet_final.png` に出力します（選定用の `out/contact_sheet.png` は上書きしません）。

合成は次の手順で行います。

1. フレーム中央の画素 (512, 768) と色差30以内でつながった領域を、アーチ窓として検出します。
2. 検出した領域の穴を埋め、3px 広げます。
3. 絵柄を窓が隠れる最小の倍率に拡大し、左右は中央揃え、上は上端揃えで切り抜きます。
4. 縁を半径1pxでぼかしたマスクを使い、フレームに貼り込みます。

窓の位置が想定（x=150〜872、y=247〜1234）から大きくずれた場合は、警告を表示します。

カード名・番号・天体記号は画像に重ねません。アプリ側で描画します。

## 小アルカナ（56枚）

仕様は `tarot-gen-minor-addendum.md`、カード定義は `cards_minor.json`（ID 22〜77）です。

| 区分 | 枚数 | 作り方 |
| --- | --- | --- |
| エース・人物札 | 20 | `generate.py --cards cards_minor.json`（大アルカナと同じ手順） |
| 数札（2〜10） | 36 | 素材を AI で生成し、`layout.py` で記号を配置 |

### 1. エース・人物札

```sh
python generate.py --cards cards_minor.json --variants 3
```

`method` が `ai` のカードだけが対象になります。

### 2. 数札用の素材（スート記号・背景、各4点）

```sh
python generate.py --assets --variants 3                 # 8点×3案
python generate.py --assets --only wands,bg_cups         # スート名や素材名で絞り込む
python composite.py --assets-sheet --no-composite        # 素材の一覧 out/contact_sheet_assets.png
```

- 出力先は `assets/symbol_{suit}_{案}.png`（背景透過）と `assets/bg_{suit}_{案}.png` です。
- 素材のプロンプトには、style.txt から人物・光輪・構図の行を除いた `style_asset.txt` を使います。
- Codex 標準の画像生成は透過 PNG を出力できます（2026-09-30 に実測で確認済み）。
- 採用案は `selected_assets.json` に記入します。例：`{"symbol_wands": "a", "bg_wands": "b", ...}`

### 3. 数札の配置（layout.py）

```sh
python layout.py                 # 36枚すべて
python layout.py --only cups     # スート名またはカードIDで絞り込む
python test_layout.py            # 記号の個数・重なりの自動テスト
```

- 出力先は `out/raw/{id:02d}_{slug}_a.png` で、`selected.json` に `a` として自動で記入されます。
- スートごとの配置方式は `layout.py` の `SUIT_CONFIG` と `layout_config.json` で決まります。
- どのスートも、記号の下端が y=0.89 を超える場合と、合成後にフレームで隠れる部分がある場合は、警告を表示します。

#### カップ・ペンタクル（格子配置）

- 記号の位置・大きさは、追補の §3 に従います。重なる場合は、自動で5%ずつ縮小します。
- 記号の周囲の背景を柔らかく暗くします（暗い後光、濃さ85%）。

#### ワンド・ソード（手描きのデザイン、2026-10-01 確定）

ワンドとソードの数札は、総司が手でデザインした `designs/` の画像を使います。

```sh
python import_design.py            # 取り込み（検証 → 影の付与 → 背景と合成 → selected.json を "h" に）
python import_design.py --check    # 検証だけ（フレームで隠れる部分、下端 y=0.89）
python composite.py                # フレームと合成
```

- 入力：`designs/Sword_design{2..10}.png`、`designs/wand_design{2..10}.png`（1024×1536、背景透過、記号だけ。背景の画像と同じ座標）
- 影：カップ・ペンタクルと同じ「暗い後光」（濃さ85%）とドロップシャドウ（不透明度18%）を付けます。値は `layout.py` の `HALO_*`・`SHADOW_*` を使います。
- 背景：`selected_assets.json` で採用した `assets/bg_{suit}_*.png` に合成し、`out/raw/{id:02d}_{slug}_h.png`（h＝手描き）に保存します。`layout.py` は a 案しか書かないため、上書きされません。
- デザイン用の素材（記号単体の透過 PNG、スート別のフレーム画像、目安線のレイヤー）は `out/design_kit/` に作ってあります（Git の管理対象外）。

以下のワンド・ソードの自動配置（トレース構図と size_tuner）は、手描きのデザインに切り替える前の試作の仕組みとして残してあります。

#### ワンド・ソード（ラフのトレース、`crossed.py`、`handoff-swords-trace.md`・`handoff-wands-swords-unify.md`）

- ワンドとソードは同じ骨格 `swords_traced.json` を使います。ワンドは、剣の柄頭 → 杖の下端、切っ先 → 杖の上端に対応させます（花飾りは使いません）。
- 光背の円は `layout_config.json` の `wands.circle`（中心 (512, 611)、R=350）と `swords.circle`（中心 (512, 469)、R=322）です。
- ワンドは明度 +15%・彩度 +10% に補正します。

- 位置は、総司のラフ `refs/sword_rough.png` から剣1本ずつの柄頭と切っ先をトレースした `swords_traced.json` に従います。
  - 座標は光背の円の中心を原点、R を単位とし、y は下向きです。
  - 描画順はファイルの並び順です。剣どうし・ユニットどうしの重なりは意図したものです。
- 素材は、上端・下端・中心線を計測して位置を合わせます（画像の中心は使いません）。
- 太さ：全体を長さに合わせて縦横同率に縮めたうえで、**剣は刃（切っ先〜鍔の上端）、杖は軸（両端の若葉の飾りを除いた部分）だけを横方向に太くし**、拡大後の4の幅にそろえます。柄と若葉の飾りは変形させません。
  - 太くする量は最大 +100% です。剣は、太くした刃の幅が鍔の幅の70%を超えると警告します。
- 光背の円による制限はありません。全要素がアーチ窓の内側（縁から 0.02R の余白）と下端 y=0.89 に収まるかを検証します。
- 大きさ（拡大率）と上下位置は、下記の size_tuner で目で決めます。

#### ワンド・ソードの大きさの調整（size_tuner）

ワンドとソードの数札は、同じ `swords_traced.json` の骨格を使います（ワンドは柄頭→杖の下端、切っ先→杖の上端）。大きさと上下位置は、規則ではなく目で決めます。

```sh
python size_tuner.py        # ブラウザで http://127.0.0.1:8765/ を開く（終了は Ctrl+C）
```

- スートと枚数を選び、拡大率（0.8〜3.0、光背の円の中心が基準）と上下位置（±0.3R、下向きが正）をスライダーで調整します。
- 右側のカードは `layout.py` と同じ処理で描いたフレーム合成後の見た目で、左に同じ枚数のカップを並べます。
- アーチ窓（縁から 0.02R の余白）または下端 y=0.89 を超えると、カードの枠と警告欄が赤くなります（調整はそのまま続けられます）。
- 「layout_config.json に書き出す」で `{suit}.size` に保存します。直前のファイルは `out/review/layout_config.backup.json` に残ります。
- 刃・杖の軸の太さは、拡大後の 4 を基準にそろえます。4 の拡大率を変えると、ほかの枚数の太さも変わります。
- `size` に値のない枚数は、`handoff-wands-swords-unify.md` §3 の自動規則で大きさを決めます。

`swords_traced.json` の作り方：

1. `python trace_swords.py` で自動の下書きを作ります。ラフのカードを画像照合で出力と同じ座標に重ね（`fit_rough.py`）、剣を1本ずつ動かしてラフに重ねます。
2. `python trace_grid.py 6 t` のように、0.1R の目盛りとトレース線を重ねたラフの拡大画像（`out/review/trace_grid_*.png`）を作り、ずれている座標を手で直します（2026-09-30 の作成時は、4〜10 を手で読み取りました）。
3. `python trace_swords.py --overlay-only` で、ラフに赤い線を重ねた `out/review/swords_trace_overlay.png` を出力し、全カードで重なっていることを目で確認します。
4. `python layout.py --only swords --out-dir out/review/rough` と `python review_rough.py` で、ラフと出力の比較画像 `out/review/swords_rough_compare.png` を作って確認します。

### 4. 一覧と合成

```sh
python composite.py --contact-sheet --suit minor --choices-only --no-composite  # 選定用：案が複数あるカードの全案（out/contact_sheet_{suit}.png）
python composite.py --contact-sheet --final --suit minor --no-composite         # スート別の決定稿一覧（out/contact_sheet_{suit}_final.png）
python composite.py                                                       # selected.json の全カードを合成
```
