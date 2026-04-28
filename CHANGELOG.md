# Changelog

[Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) 形式 / [Semantic Versioning](https://semver.org/lang/ja/)

## [0.4.0] - Phase 4

### Added
- F-06 PDF レポート出力 (元 Excel + 注釈オーバーレイ + サマリ + PT 候補)
- F-09 指摘対応管理 (未着手 / 対応中 / 完了 / 対象外)
- PDF 生成ジョブの非同期化 (`POST /reviews/:id/generate_pdf` → ポーリング → DL)
- Excel→PDF 変換の二段構え (Excel COM / LibreOffice 自動切替)

### Changed
- `Review` モデルに `pdf_status` / `pdf_path` / `pdf_generated_at` を追加
- Frontend のレビュー結果ページに PDF DL ボタン + 状態ポーリング
- 指摘詳細ダイアログで対応状況を更新可能に

## [0.3.5] - Phase 3.5

### Added
- F-03 D&D 1 画面投入 UX (観点ファイル / UI / SS をドラッグ＆ドロップ)
- F-07 横断レビュー (UI×SS 整合性チェック)
- `ReviewCreate` に `review_type` / `target_artifact_ids` / `aspect_artifact_id` を追加
- HTML5 Drag and Drop API ベースの `Dropzone` コンポーネント

### Changed
- レビュー作成 API を旧 (`artifact_id`) と新 (`target_artifact_ids[]`) の両対応に
- レビュー実行ページを D&D 1 画面構成に再設計

## [0.3.0] - Phase 3

### Added
- F-05 観点ファイル方式 (Excel / TXT、PM 提供)
- 観点パーサ (`aspect_parser.py`) — Excel 読み + メタデータ抽出
- Anthropic Claude クライアント (本番用、tenacity リトライ付き)
- `LLM_PROVIDER` 環境変数による Stub / Anthropic 切替
- PII マスキング層 (`pii_masking.py`)

### Changed
- レビュー engine を観点単位ループに再構築
- LLM 呼び出しに `asyncio.timeout` + bounded concurrency (Semaphore) 導入

## [0.2.0] - Phase 2

### Added
- F-03 AI レビュー実行 (BackgroundTasks)
- F-04 レビュー結果表示 (指摘一覧 / 詳細 / フィルタ)
- Stub LLM クライアント (固定指摘 2 件返却)
- `Review` / `Finding` / `FindingResponse` モデル
- レビューステータスポーリング (3 秒間隔)

## [0.1.0] - Phase 1

### Added
- F-01 プロジェクト管理 (CRUD)
- F-02 成果物管理 (アップロード / 版管理 / DL)
- F-08 ユーザ認証 (JWT + bcrypt)
- 認可: `project.owner_id == current_user.id`
- Alembic マイグレーション基盤
- Frontend: Next.js 14 App Router + 認証ガード (`(authed)` ルートグループ)
- Backend: FastAPI + SQLAlchemy 2.x asyncio + Pydantic v2

[0.4.0]: ./
[0.3.5]: ./
[0.3.0]: ./
[0.2.0]: ./
[0.1.0]: ./
