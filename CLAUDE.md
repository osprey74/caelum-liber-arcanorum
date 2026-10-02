# caelum-liber-arcanorum — Liber Arcanorum

タロット占いアプリ（個人利用）。ラテン語で「秘儀の書」。
姉妹アプリ Liber Caeli（`g:\dev\caelum`、西洋占星術）と同じ Caelum シリーズ。

## 技術スタック
- フロントエンド: Tauri v2, React 19, TypeScript, Tailwind CSS 3, Vite 7
- バックエンド: Rust（Tauri）。Python のサイドカーは使わない
- AI: Anthropic Claude API。Rust（`src-tauri/src/interpret.rs`）から HTTPS で直接呼び出す。APIキーは keyring（`com.osprey74.liberarcanorum`）、モデルは `%APPDATA%\liber-arcanorum\config.json`、システムプロンプトは `src/data/interpret-system.md`
  - 相談窓口の判定は `src/lib/crisis.ts`、文面は `src/data/support.ts`。番号を変えるときはシステムプロンプトの #9110・#8008 も直す
  - 生成例の確認：`LA_SAMPLE_DIR=<dir> npx vitest run src/lib/samples.node.test.ts` のあと `cd src-tauri && cargo test live_samples -- --ignored`（API の料金がかかる）
- カード絵柄の生成ツール: `tools/tarot-gen/`（Python 3.11、Pillow・numpy・opencv-python）

## ディレクトリ
- `src/`         React フロントエンド
  - `src/components/`  UI コンポーネント
  - `src/data/`        カードのマニフェスト・意味・スプレッドの定義（JSON）
  - `src/assets/cards/` カード画像（WebP、`tools/tarot-gen/build_assets.py` で生成）
  - `src/types/`       型定義
- `src-tauri/`   Tauri 設定・Rust コード
- `tools/tarot-gen/` カード絵柄の生成・合成ツール（アプリには同梱しない。README 参照）
- `site/`        紹介サイト（Astro、bun）。https://arcanorum.osprey74.com に `.github/workflows/site.yml` で FTP 配置
- `.github/workflows/release.yml` Windows インストーラー（タグ `v*.*.*` で下書きリリース）

## 開発コマンド
```bash
npm install            # 初回
npm run tauri dev      # 開発起動
npm run build          # フロントエンドのビルド（型チェック込み）
cd src-tauri && cargo check
```

`tools/tarot-gen/` のスクリプトは `py -3.11 <script>.py` で実行する（既定の `python` が別の Python を指す環境があるため）。

## 作業の進め方
- アプリ実装は `handoff-app-implementation.md` のフェーズ1〜5に従う。各フェーズの終わりで止めて報告し、承認を得てから次へ進む。
- 姉妹アプリ caelum の実装を流用する場合は、先に調査して方針を報告する。

## バージョン
- 更新対象: `package.json`, `src-tauri/Cargo.toml`, `src-tauri/tauri.conf.json`
- バージョン更新後は `cargo generate-lockfile` で `Cargo.lock` を更新する
- 紹介サイトの `site/src/content.ts` の `VERSION`・`SIZE_MB` も合わせて更新する

## コーディング規約
- TypeScript: strict mode、型定義は `src/types/` に集約
- コミット: Conventional Commits（feat/fix/docs/refactor/chore）

## 注意事項
- APIキーなどの秘密情報をコード・ログ・リポジトリに含めない（`.env` はコミット禁止）
- カード名・番号・天体記号は画像に含めず、アプリ側で重ね描きする
- 記号（天体・星座・元素）はフォントの文字ではなく SVG で描画する
