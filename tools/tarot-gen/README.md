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
|---|---|
| `cards.json` | 22枚のカード定義（正本）。人物の性別はライダー・ウェイト・スミス版の伝承に従う |
| `style.txt` | 固定のスタイル指定（変更する場合は事前に合意すること） |
| `refs/style_ref.png` | 画風の参照画像 |
| `refs/frame.png` | 共通フレーム |
| `refs/backimage.png` | カード裏面 |
| `selected.json` | 採用案のリスト（手で記入する） |
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
|---|---|
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

合成は次の手順で行います。

1. フレーム中央の画素 (512, 768) と色差30以内でつながった領域を、アーチ窓として検出します。
2. 検出した領域の穴を埋め、3px 広げます。
3. 絵柄を窓が隠れる最小の倍率に拡大し、左右は中央揃え、上は上端揃えで切り抜きます。
4. 縁を半径1pxでぼかしたマスクを使い、フレームに貼り込みます。

窓の位置が想定（x=150〜872、y=247〜1234）から大きくずれた場合は、警告を表示します。

カード名・番号・天体記号は画像に重ねません。アプリ側で描画します。
