# ポートフォリオ向け技術ハイライト

このドキュメントは、本リポジトリを技術ポートフォリオとして読む方 (採用担当・面接官・技術リード) 向けに、設計判断と実装上の工夫を簡潔にまとめたものです。

## このプロジェクトの位置づけ

SI/SES 業界のウォーターフォール開発で、**「完璧であるべき設計書」のレビュー作業を AI で自動化** する PoC。

- **対象工程**: 詳細設計 (UI 機能概要書 / SS 構造設計書)
- **対象組織**: 顧客レビュー前の社内品質確保フェーズ
- **削減対象**: 「人間レビュアーが見落としやすい曖昧表現・条件分岐漏れ・横断仕様食い違い」

## 設計上の主要判断

### 1. AI クライアントを Protocol で抽象化

```python
class LLMClient(Protocol):
    async def review(self, *, prompt, system, timeout_s) -> LLMReviewResult: ...
```

- **本番**: Anthropic Claude (`AnthropicClient`)
- **開発/CI**: 固定指摘を返す `StubLLMClient` — **API キー不要・課金 0**
- 環境変数 `LLM_PROVIDER` で切替

→ ローカル開発と CI で **コスト 0** を担保しつつ、本番は最小コードで本物 LLM に切替可能。

### 2. レビュー実行は BackgroundTasks + ポーリング

同期 API でレビューを完結させると 30 秒〜数分間 HTTP コネクションを保持することになる。

- API は `202 Accepted + review_id` で即返却
- 実処理は FastAPI `BackgroundTasks` で非同期実行
- フロント側は React Query の `refetchInterval` で 3 秒ポーリング、`status=completed/failed` になったら停止

→ シンプルで運用負荷が低い。スケールが必要になれば Celery / RQ への置換が容易。

### 3. PDF 生成は二段構え

```
Excel → PDF (Excel COM or LibreOffice) → 注釈オーバーレイ (PyMuPDF)
```

- **Excel COM** (Windows + Office): 最も忠実。図形・色・印刷範囲が崩れない
- **LibreOffice fallback** (Linux): クラウドネイティブ運用用
- 環境変数 `EXCEL_TO_PDF_BACKEND=auto` で自動選択

→ 「本番は Windows Server EC2、開発/CI は Linux」という現実的な構成に対応。

### 4. PII マスキング層を LLM 送信直前に挿入

```python
class PiiMaskRule:
    pattern: re.Pattern
    replacement: str  # "[氏名]" 等
```

LLM への送信前に氏名・社名・電話・メールを伏字化。ルールは dataclass で拡張可能。

### 5. 認可は API レイヤで一元化

```python
async def get_project_for_user(db, owner_id, project_id) -> Project: ...
```

全ての保護リソース API は最初にこの関数を呼ぶ。`project.owner_id == current_user.id` を満たさない場合は 404 (情報漏洩防止のため 403 ではなく 404)。

## テスト戦略

| 層 | フレームワーク | 件数 | カバー範囲 |
|---|---|---|---|
| API 層 | pytest + httpx | 中心 | 認証・認可・バリデーション・正常系/異常系 |
| Service 層 | pytest + pytest-asyncio | 主要関数 | レビュー engine / PDF 生成 / aspect parser |
| Frontend | vitest + Testing Library | 19 件 | ロジック関数・主要コンポーネント |
| **合計** | | **94 件** | CI で全件実行 |

Stub LLM のおかげで **AI 呼び出しを含む E2E テストが課金 0 で回る**。

## 開発プロセスの工夫 (PM/PG 役割分離)

```
[PM 役]  ─ 設計書作成 → Phase 設計 → コードレビュー → 議論 → 修正承認
[PG 役]  ─ Phase ごとに実装 → 報告 → 議論受け答え → 修正実装
```

- 設計と実装を **明示的に分離**することで、個別の品質基準を保ちながら高速反復
- 「指摘 → 同意 / 反論 + 技術的根拠 → 議論」のループ
- Phase 単位 (1→2→3→3.5→4) の漸進実装により、各段階で動くものを保ちながら拡張

## 機能と実装フェーズの対応

| Phase | 主な実装 | 結果 |
|---|---|---|
| 1 | 認証 / プロジェクト / 成果物管理の基盤 | F-01, F-02, F-08 |
| 2 | レビュー実行 (BackgroundTasks + Stub LLM) | F-03, F-04 |
| 3 | 観点ファイル方式 + Anthropic 切替 | F-05 |
| 3.5 | D&D 1 画面投入 + 横断レビュー | F-03 (UX 改善), F-07 |
| 4 | PDF レポート出力 + 指摘対応管理 | F-06, F-09 |

## ディレクトリ全体感

詳細は [README.md](../README.md) のディレクトリ構成を参照。

```
backend/   レイヤ分離 (api / services / parsers / llm / models / schemas)
frontend/  Next.js App Router + 機能単位ページ (login / projects / projects/[id]/...)
docs/      アーキテクチャ・セットアップ・デモ・本ドキュメント
samples/   検証用モック Excel (架空の ABC 社案件想定)
.github/   CI 定義 + Issue テンプレート
```

## 想定される質問と回答

**Q. なぜ Next.js App Router を選んだか？**
A. RSC によるサーバ側データ取得と Client Component の使い分けで、認証ガード (`(authed)` ルートグループ) と公開ページ (`/login`) を URL ベースで明確に分離できる。Pages Router より境界が綺麗。

**Q. なぜ FastAPI を選んだか？**
A. Pydantic v2 によるバリデーションと OpenAPI 自動生成。型ヒントを書くだけで API ドキュメントとリクエスト検証が完成するため、設計書 (= API 定義) と実装の乖離が起きにくい。

**Q. なぜ SQLAlchemy 2.x asyncio？**
A. FastAPI が asyncio で動くため、DB アクセスを同期にすると性能利点が消える。SQLAlchemy 2.x は同期/非同期を統一 API で扱える。

**Q. PostgreSQL を本番に選ぶ理由？**
A. JSONB / 配列型で `target_artifact_ids` / `aspect_ids` を素直に保存できる。SQLite は開発のみ。

**Q. 認証に Auth0 / Cognito を使わない理由？**
A. PoC の単純さ優先。本番運用では JWT 自前管理を Cognito / Auth0 に置換する想定。

**Q. AI 利用料の見積りは？**
A. Stub LLM では 0。Anthropic Claude は 1 レビュー (観点 10 個 × 設計書 1 ページ程度) で概ね 5〜10 円。観点ファイル粒度と設計書ボリュームに線形依存。

## 既知の制約・改善余地

- **Stub LLM の指摘は固定 2 件**。実用評価は Anthropic 切替必須
- **大量ファイル (>10MB)** のストリーミング未対応
- **Findings の学習機能** (`knowledges` テーブル) はスキーマのみで未実装
- **同時実行レビュー数** は環境変数 `MAX_CONCURRENT_REVIEWS` で制限。本番は専用 worker (Celery 等) 推奨
- **マルチテナント** は未対応 (1 owner = 1 ワークスペース)

## License

MIT。商用利用可。改変フォーク歓迎。
