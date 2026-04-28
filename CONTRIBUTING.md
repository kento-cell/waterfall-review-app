# Contributing

本リポジトリは PoC (Proof of Concept) として公開しています。フォーク・改変・実験は歓迎します。

## ローカル開発

[docs/setup.md](docs/setup.md) を参照。

## ブランチ運用

- `main` を保護ブランチ扱い
- 機能追加: `feature/<topic>` → PR → `main`
- バグ修正: `fix/<topic>` → PR → `main`

## コミットメッセージ

[Conventional Commits](https://www.conventionalcommits.org/ja/v1.0.0/) 推奨。

```
feat(api): add cross review endpoint
fix(frontend): handle 401 in axios interceptor
docs: update setup.md for LibreOffice path
test(review): add aspect parser edge case
```

## コードスタイル

| 言語 | フォーマッタ | リンタ |
|---|---|---|
| Python | `ruff format` | `ruff check` / `mypy` |
| TypeScript | `prettier` | `eslint` (Next.js デフォルト) |

PR 前に `pytest` / `npm test` / 型チェックを通すこと。CI も同じものを走らせます。

## PR チェックリスト

- [ ] CHANGELOG.md に追記
- [ ] テスト追加 (新機能 / バグ修正)
- [ ] `pytest` / `npm test` 通過
- [ ] 型チェック通過 (`mypy` / `tsc --noEmit`)
- [ ] 機密情報を含めない (顧客名・実 API キー・実データ)

## Issue を立てる前に

- 既存 Issue を検索
- バグ報告は再現手順を必ず記載 ([テンプレ](.github/ISSUE_TEMPLATE/bug_report.md))
- 機能要望は背景・動機を必ず記載 ([テンプレ](.github/ISSUE_TEMPLATE/feature_request.md))

## ライセンス

このリポジトリへの貢献は MIT License で公開されることに同意したものとみなします。
