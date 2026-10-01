# Liber Arcanorum

Caelum シリーズのタロット占いアプリです（姉妹アプリ：Liber Caeli）。Tauri v2・React・TypeScript で作っています。

## 開発

```sh
npm install
npm run tauri dev
```

カード絵柄の生成・合成ツールは `tools/tarot-gen/` にあります（`tools/tarot-gen/README.md`）。画像は Git LFS で管理しています。

## 素材のライセンスと出典

### カード絵柄

78枚のカード絵柄、フレーム、裏面は、このプロジェクトのために作成したものです。

### フォント

カード名のプレートには **Shippori Mincho SemiBold** を使います（2026-10-01 決定）。SIL Open Font License 1.1（OFL）のもと、アプリに同梱しています（CDN からは読み込みません）。

| 項目 | 内容 |
| --- | --- |
| 書体 | Shippori Mincho SemiBold |
| 著作権者 | Copyright 2021 The Shippori Mincho Project Authors（https://github.com/fontdasu/ShipporiMincho） |
| 出典 | https://github.com/google/fonts/tree/main/ofl/shipporimincho |
| ライセンス | SIL Open Font License 1.1。本文は `src/assets/fonts/ShipporiMincho-OFL.txt`（元の TTF とともに `tools/fonts/` にも同梱） |
| 同梱の形 | 使用する文字だけに絞ったサブセット（WOFF2、約29KB）。`tools/fonts/build_fonts.py` で作成 |

OFL の条件により、サブセットにした書体も同じライセンスで配布しています。

#### サブセットの対象文字

アプリには、次の文字だけに絞った Shippori Mincho を同梱しています（119文字、2026-10-01 時点）。

- `src/data/cards.json` の全カードの日本語名（`name_ja`）、ローマ数字（`roman`）、英語名（`name_en`）に出てくる文字
- `tools/fonts/build_fonts.py` の `EXTRA_TEXT` に書いた文字（数字、ローマ数字の I V X L C D M、空白、「・ー」、「正逆位置表裏面」）

```text
 0123456789ACDEFHIJKLMNPQSTVWXacdefghilmnoprstuvwx　さたのるれイエカキクグジスソタットドナプペルワン・ー世人位判制力吊命塔太女審帝師恋悪愚戦教星月正死男界皇神節置義者術表裏車輪逆運陽隠面魔
```

対象文字を追加する手順（意味の文章など、カード名以外にも Shippori Mincho を使う場合）：

1. 追加したい文字を `tools/fonts/build_fonts.py` に加えます。
   - 少しだけ足す場合は、`EXTRA_TEXT` に文字を書き足します。
   - 意味の文章（`src/data/meanings.json` など）を丸ごと対象にする場合は、`charset()` でそのファイルの文字列も読み込むようにします。
2. `py -3.11 tools/fonts/build_fonts.py` を実行し、`src/assets/fonts/shippori-mincho-semibold.woff2` を作り直します。
3. 表示に使う文字がすべて含まれているかを、ギャラリー画面などで確認します。含まれない文字は別の書体（システムの明朝体）で表示されるため、見た目が混ざります。
4. 作り直した WOFF2 をコミットします（元の TTF は `tools/fonts/` に Git LFS で保存しています）。

文章全体を対象にすると、ファイルが大きくなります（常用漢字を含めると数百KB〜1MB程度）。その場合は、本文だけ別のシステム書体にする方法も検討してください。

### 記号の SVG

メダリオンの天体7種・星座12種・元素4種の記号は、このプロジェクトで描いたオリジナルの SVG パスです（`src/components/Glyph.tsx`）。フォントの文字は使っていません。
