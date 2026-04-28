# Slides — 概要スライド自動生成

`Waterfall Review App` の 12 ページ概要スライドを **コードから生成** する仕組みです。Node.js だけで動き、PowerPoint や macOS Keynote 等の編集ソフトは不要。

> **Why コード生成?**
> デザインを Git でレビュー可能にし、内容変更 (実装の進捗・テスト件数等) を 1 行の差分で反映できるようにするため。手作業の PowerPoint は属人化・差分追跡不能になりがち。

## クイックスタート (3 コマンド)

```bash
cd slides
npm install
npm run build
```

→ `slides/dist/Waterfall_Review_App_Overview.pptx` (約 380KB / 12 ページ) が生成される。

## 必要環境

| 必須 | バージョン |
|---|---|
| Node.js | 18 以上 |
| OS | Windows / macOS / Linux いずれも可 |

PowerPoint・Office・Keynote 等の **インストールは不要**。生成された `.pptx` は任意のソフト (PowerPoint, Keynote, Google Slides, LibreOffice Impress) で開ける。

## どこでも生成できる仕組み

| 場所 | 方法 |
|---|---|
| ローカル PC | `cd slides && npm install && npm run build` |
| GitHub Actions | main / PR push で自動ビルド → Artifacts からダウンロード ([.github/workflows/slides.yml](../.github/workflows/slides.yml)) |
| Docker / コンテナ | `docker run --rm -v $PWD:/app -w /app/slides node:20 sh -c "npm install && npm run build"` |
| Codespaces / Dev Container | Node.js が入っていればそのまま `npm run build` |

## ファイル構成

```
slides/
├ README.md         このファイル
├ package.json      依存定義 (pptxgenjs のみ)
├ package-lock.json 依存ロック
├ generate.js       12 スライド生成スクリプト (約 900 行)
├ .gitignore        node_modules/ + dist/
└ dist/             ビルド成果物 (gitignore)
   └ Waterfall_Review_App_Overview.pptx
```

## スライド構成 (12 ページ)

| # | タイトル |
|---|---|
| 1 | カバー (Waterfall Review App / Phase 1〜4 完了) |
| 2 | 何を解決するか (Why) |
| 3 | UI 機能概要書 vs SS 構造設計書 の位置づけ |
| 4 | システム構成 (AWS Windows Server EC2 想定) |
| 5 | 利用フロー (5 ステップ) |
| 6 | 投入画面 (D&D 1 画面) |
| 7 | レビュー結果 (PDF オーバーレイ) |
| 8 | PDF 構造 (原本 + サマリ + PT 候補) |
| 9 | 工程別の機能切替 (UI / SS / UI×SS) |
| 10 | AI コスト (開発 ¥0 / 本番試算) |
| 11 | 進捗 (Phase 1〜4 完了 / Phase 5+ ロードマップ) |
| 12 | まとめ + リポジトリの読み方 |

## カスタマイズ

`generate.js` 冒頭のデザインシステム (`C` カラー / `F` フォント) を編集すれば配色・フォントを変更可能。日本語フォントは Yu Mincho / Yu Gothic を既定としているため、表示環境に応じて差し替え推奨。

各スライドは `// =====` のコメントで区切られた独立ブロック。スライド単位でテキスト・配置を編集可能。

## ライブラリ

- [pptxgenjs](https://gitbrent.github.io/PptxGenJS/) v4.x — JavaScript で PPTX を生成

## License

本ツール部分は親リポジトリと同様に [MIT License](../LICENSE) で公開。
