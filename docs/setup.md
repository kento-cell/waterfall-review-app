# セットアップ

## 前提

| 必須 | バージョン | 用途 |
|---|---|---|
| Python | 3.11 以上 | Backend |
| Node.js | 20 以上 | Frontend |
| Git | 任意 | clone / 作業 |

| 任意 | 補足 |
|---|---|
| PostgreSQL 15+ | 本番想定。開発は SQLite で OK |
| LibreOffice | Linux/Mac で Excel→PDF 変換に使用 |
| Microsoft Excel | Windows 環境で COM 経由の高精度 PDF 変換 |
| Anthropic API キー | 本番 LLM 呼び出し。未設定でも `LLM_PROVIDER=stub` で動作 |

## クイックスタート

```bash
git clone <this-repo>
cd waterfall-review-app
```

### Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / Mac
source .venv/bin/activate

python -m pip install -e ".[test]"
python -m alembic upgrade head

# Stub LLM で起動 (Anthropic API キー不要 / 課金 0)
LLM_PROVIDER=stub uvicorn app.main:app --port 8000 --reload
```

API ドキュメント: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

UI: http://localhost:3000

### 初期ユーザ作成

API 経由で作成 (POST `/api/auth/register`):

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@example.com",
    "password": "password123",
    "display_name": "Demo User"
  }'
```

## 環境変数

### Backend (`backend/.env`)

| キー | 例 | 説明 |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./app.db` | SQLAlchemy URL。本番は PostgreSQL を推奨 |
| `JWT_SECRET_KEY` | 32 バイト以上のランダム値 | 本番は必ず変更 |
| `JWT_ALGORITHM` | `HS256` | デフォルト |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | アクセストークン有効期限 |
| `LLM_PROVIDER` | `stub` / `anthropic` | レビュー LLM 切替 |
| `ANTHROPIC_API_KEY` | `sk-ant-...` | `LLM_PROVIDER=anthropic` 時に必須 |
| `STORAGE_DIR` | `./storage` | アップロードファイル保存先 |
| `PDF_OUTPUT_DIR` | `./storage/pdf` | レビュー PDF 出力先 |
| `EXCEL_TO_PDF_BACKEND` | `auto` / `excel_com` / `libreoffice` | Excel→PDF 変換手段 |
| `CORS_ORIGINS` | `http://localhost:3000` | カンマ区切り |

### Frontend (`frontend/.env.local`)

| キー | 例 |
|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` |

## テスト実行

```bash
# Backend (pytest 75 件)
cd backend
pytest -q

# Frontend (vitest 19 件)
cd frontend
npm test
```

## 本番ビルド

```bash
# Frontend
cd frontend
npm run build
npm run start

# Backend (gunicorn + uvicorn worker)
cd backend
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 既知の制約

- **Stub LLM** は固定 2 件の指摘しか返さない。実用評価には Anthropic API キーが必要。
- **Excel COM** は Windows + Microsoft Excel が必要。Linux/Mac では LibreOffice を使う。
- **PostgreSQL** は本番想定。SQLite では同時書込でロックする可能性あり (PoC 用途では問題なし)。
- 大量ファイル (>10MB) のアップロードは未最適化。本番では multipart streaming に変更推奨。
