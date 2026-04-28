from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import artifacts, aspects, auth, findings, projects, reviews
from app.core.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0")

# CORS (フロント開発サーバ http://localhost:3000 等からのアクセス許容)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(aspects.router, prefix="/api/aspects", tags=["aspects"])
app.include_router(artifacts.router, tags=["artifacts"])
app.include_router(reviews.router, tags=["reviews"])
app.include_router(findings.router, tags=["findings"])


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
