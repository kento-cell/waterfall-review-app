# AIレビュー支援ツール — フロントエンド (Phase 3)

Next.js 14 (App Router) + TypeScript + Tailwind CSS + React Query + Zustand。
Phase 1+2 のバックエンド (FastAPI) と通信して、ログイン → プロジェクト管理 → 成果物アップロード まで動作する。

## 起動手順 (開発)

```bash
# 1. 依存インストール
npm install

# 2. (任意) API URL を上書き (.env.local)
#    既定で .env.local が NEXT_PUBLIC_API_URL=http://127.0.0.1:8001 を設定済
#    バックエンドのポートに合わせて編集

# 3. バックエンドを起動 (別シェル)
cd ../backend
LLM_PROVIDER=stub uvicorn app.main:app --port 8001

# 4. フロント開発サーバ起動
npm run dev

# 5. ブラウザで http://localhost:3000 を開く
```

## 主なスクリプト

| スクリプト | 内容 |
|---|---|
| `npm run dev` | 開発サーバ (http://localhost:3000) |
| `npm run build` | プロダクションビルド |
| `npm start` | プロダクションサーバ |
| `npm run lint` | ESLint |
| `npm test` | vitest |
| `npm run type-check` | tsc --noEmit |

## ディレクトリ構成

```
frontend/
├ src/
│  ├ app/
│  │  ├ layout.tsx               (root layout + Providers)
│  │  ├ page.tsx                 (/ → /projects リダイレクト)
│  │  ├ globals.css
│  │  ├ providers.tsx            (React Query)
│  │  ├ login/page.tsx           (SC-01)
│  │  └ (authed)/                (認証必須グループ)
│  │     ├ layout.tsx            (Header + Sidebar + 認証ガード)
│  │     ├ projects/page.tsx     (SC-02)
│  │     └ projects/[id]/
│  │        ├ page.tsx           (SC-03)
│  │        └ artifacts/upload/page.tsx  (SC-04)
│  ├ components/
│  │  ├ ui/                      (button, input, label, card, table, dialog)
│  │  └ layout/                  (header, sidebar)
│  ├ lib/
│  │  ├ api/                     (client, auth, projects, artifacts)
│  │  └ utils.ts
│  ├ store/auth.ts               (Zustand + localStorage 永続化)
│  ├ types/api.ts                (バックエンド Pydantic 整合)
│  └ __tests__/                  (vitest)
├ package.json
├ tsconfig.json
├ next.config.mjs
├ tailwind.config.ts
├ postcss.config.mjs
├ vitest.config.ts
├ .env.example
└ .env.local
```

## 認証フロー

1. `/login` でメール+パスワード入力
2. POST `/api/auth/login` → JWT 取得
3. JWT を Zustand + localStorage に保持
4. `(authed)` グループ配下は layout で認証ガード (token 無ければ /login リダイレクト)
5. axios interceptor が自動で Authorization ヘッダ付与
6. 401 受領時は localStorage クリア → /login リダイレクト

## テスト

```bash
npm test
```

カバー範囲 (Phase 3):
- utils (cn / formatBytes / formatDateTime)
- auth store (Zustand)
- LoginPage (フォーム送信 + バリデーション)

E2E (Playwright) は Phase 8 で実装予定。

## Phase 4 以降の連携点

- レビュー実行画面 (SC-05) → 観点選択 + 対象成果物選択
- レビュー結果画面 (SC-06) → 指摘一覧
- 指摘詳細 (SC-07) → 対応状況更新

API は既に backend/app/api/reviews.py / findings.py で実装済 (Phase 2)、
本フェーズでは UI 側 disabled プレースホルダ。
