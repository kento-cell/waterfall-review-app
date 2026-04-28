from __future__ import annotations

from app.core.config import settings
from app.llm.anthropic_client import AnthropicClient
from app.llm.base import LLMClient
from app.llm.stub_client import StubLLMClient


def get_llm_client() -> LLMClient:
    provider = settings.llm_provider.lower()
    if provider == "stub":
        return StubLLMClient()
    if provider == "anthropic":
        return AnthropicClient(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
            max_tokens=settings.anthropic_max_tokens,
        )
    raise RuntimeError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")
