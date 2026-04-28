# Waterfall Review App

> **ウォーターフォール開発の成果物 (UI 機能概要書 / SS 構造設計書) を AI で自動レビューする Web アプリケーション**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=flat&logo=next.js&logoColor=white)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-06B6D4?style=flat&logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-94%20passing-success)](https://github.com/)

## 何ができるか

SI/SES 業界のウォーターフォール開発で「**完璧であるべき設計書**」のレビュー作業を AI で自動化します。

- **UI レビュー** — 機能概要書 (顧客向け) の曖昧表現・必須項目欠落を検出
- **SS レビュー** — 構造設計書 (PG/PT 向け) の条件分岐網羅・PT項目漏れを検出
- **UI×SS 整合性レビュー** — UI と SS の対応関係・仕様食い違いを横断 AI で検出
- **PDF 出力** — 元の Excel に注釈オーバーレイした PDF をワンクリック生成・DL

> **背景:** SI 現場では UI に顧客クレーム源、SS に PG/PT 漏れ源が潜む。両方の「完璧」を AI で支援。

## デモ (3 ステップ)

```
1. ログイン (JWT)
2. プロジェクト作成 → 「▶ AI レビュー実行」
3. ① 工程選択 → ② 観点ファイル D&D → ③ UI/SS D&D → ▶ 実行 → PDF DL
```

| 投入時 (D&D 1画面) | レビュー結果 + PDF DL |
|---|---|
| ![dnd](docs/screenshots/01_dnd_review_input.png) | ![result](docs/screenshots/02_review_result.png) |

## アーキテクチャ

```
┌──────────────┐  REST   ┌──────────────────┐    ┌──────────────┐
│  Next.js 14  │ ──JWT──▶│  FastAPI (asyncio)│ ──▶│ PostgreSQL    │
│  TypeScript  │         │  + BackgroundTasks │    │  (or SQLite)  │
└──────────────┘         └────┬─────────────┘    └──────────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │ Anthropic Claude │  ← Stub LLM 切替可 (開発時 課金 0)
                     │ (レビュー指摘生成) │
                     └──────────────────┘
```

詳細: [docs/architecture.md](docs/architecture.md)

## 主要技術

| カテゴリ | 採用 |
|---|---|
| Backend | Python 3.11 / FastAPI / SQLAlchemy 2.x (asyncio) / Pydantic v2 / JWT / Alembic |
| AI | Anthropic Claude API (本番) / Stub LLM (開発、API キー不要) / tenacity リトライ |
| PDF | PyMuPDF (注釈オーバーレイ) / Excel COM or LibreOffice (Excel→PDF) |
| Frontend | Next.js 14 (App Router) / TypeScript / Tailwind CSS / React Query / Zustand / React Hook Form + Zod |
| Test | pytest + httpx + pytest-asyncio (backend 75 件) / vitest + Testing Library (frontend 19 件) |
| DB | PostgreSQL (本番) / SQLite (開発) / Alembic マイグレーション |

## 機能一覧

| ID | 機能 | 状態 |
|---|---|---|
| F-01 | プロジェクト管理 | ✅ |
| F-02 | 成果物管理 (アップロード/版/DL) | ✅ |
| F-03 | AI レビュー実行 (D&D 1画面投入) | ✅ |
| F-04 | レビュー結果表示 (指摘一覧/詳細/対応状況) | ✅ |
| F-05 | 観点ファイル方式 (Excel/TXT、PM 提供) | ✅ |
| F-06 | PDF レポート出力 (原本+注釈+サマリ+PT候補) | ✅ |
| F-07 | 横断レビュー (UI×SS 整合性) | ✅ |
| F-08 | ユーザ認証 (JWT) | ✅ |
| F-09 | 指摘対応管理 | ✅ |

## クイックスタート

```bash
# Backend
cd backend
python -m pip install -e ".[test]"
python -m alembic upgrade head
LLM_PROVIDER=stub uvicorn app.main:app --port 8000

# Frontend
cd frontend
npm install
npm run dev          # http://localhost:3000
```

詳細: [docs/setup.md](docs/setup.md)

## デモシナリオ

`samples/` 配下のモック Excel を投入することで、AI レビューの流れを体験できます:

- `samples/sample_UI_機能概要書.xlsx` (UI 機能概要書、わざと「適切に処理する」等の曖昧表現を含む)
- `samples/sample_SS_構造設計書.xlsx` (SS 構造設計書、PT 項目漏れを含む)
- `samples/sample_観点_整合性.xlsx` (PM 提供の観点ファイル)

詳細: [docs/demo.md](docs/demo.md)

## 開発の進め方 (PM/PG 役割分担)

このプロジェクトは **設計者 (PM 役) と実装者 (PG 役) を明示的に分離** した協業ループで開発しました。

```
[PM 役]  設計書作成 → Phase 設計 → コードレビュー → 議論 → 修正承認
[PG 役]  Phase ごとに実装 → 報告 → 議論受け答え → 修正実装
```

- 設計と実装を分離することで、個別の品質基準を保ちながら高速反復
- レビューは「指摘 → 同意 / 反論 + 技術的根拠 → 議論」のループで品質確保

詳細: [docs/portfolio.md](docs/portfolio.md)

## ディレクトリ構成

```
.
├ backend/          FastAPI + SQLAlchemy
│  ├ app/
│  │  ├ api/        ルータ
│  │  ├ models/     SQLAlchemy
│  │  ├ schemas/    Pydantic
│  │  ├ services/   ビジネスロジック (review_engine, pdf_generation, aspect_parser 等)
│  │  ├ llm/        AI クライアント抽象化 (Anthropic / Stub)
│  │  ├ parsers/    xlsx / docx / pdf / source パーサ
│  │  └ core/       config / database / security
│  ├ alembic/       マイグレーション
│  └ tests/         pytest (75 件)
├ frontend/         Next.js 14 App Router
│  ├ src/
│  │  ├ app/        ページ (login, projects, projects/[id]/review, etc.)
│  │  ├ components/ UI 部品 (button, dropzone, finding-detail 等)
│  │  ├ lib/        api クライアント, utils
│  │  ├ store/      Zustand (auth)
│  │  └ types/      TypeScript 型
│  └ tests/         vitest (19 件)
├ samples/          検証用モック Excel
├ slides/           概要スライド自動生成 (PptxGenJS / Node.js)
├ docs/             技術ドキュメント
└ .github/          CI / Issue テンプレート
```

## 概要スライド (PPTX 自動生成)

本リポジトリには **コードから 12 ページの概要スライドを生成する仕組み** が同梱されています。Node.js だけで動き、PowerPoint・Office・Keynote のインストールは不要。

```bash
cd slides
npm install
npm run build
# → slides/dist/Waterfall_Review_App_Overview.pptx (約 380KB)
```

GitHub Actions でも自動ビルド (Artifacts からダウンロード可)。詳細: [slides/README.md](slides/README.md)

## License

[MIT License](LICENSE)

## Note

本リポジトリは PoC (Proof of Concept) として作成しました。実際のレビュー精度は AI モデルと観点ファイルの品質に依存します。Stub LLM では固定の指摘 2 件しか返らないため、実用評価には Anthropic API キーの設定が必要です。
