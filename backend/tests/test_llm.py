from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest

import app.llm.anthropic_client as anthropic_client
import app.llm.factory as factory
from app.llm.anthropic_client import AnthropicClient


class RetryableTestError(Exception):
    pass


class FakeMessages:
    def __init__(self) -> None:
        self.calls = 0
        self.max_tokens: int | None = None

    async def create(self, **kwargs: object) -> SimpleNamespace:
        self.calls += 1
        self.max_tokens = kwargs["max_tokens"]  # type: ignore[assignment]
        if self.calls < 3:
            raise RetryableTestError("temporary")
        return SimpleNamespace(
            content=[
                SimpleNamespace(type="text", text="ok"),
            ]
        )


@pytest.mark.asyncio
async def test_anthropic_client_retries_retryable_errors_and_uses_configured_max_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    messages = FakeMessages()
    client = AnthropicClient.__new__(AnthropicClient)
    client._client = SimpleNamespace(messages=messages)
    client._model = "test-model"
    client._max_tokens = 1234
    monkeypatch.setattr(
        anthropic_client,
        "_is_retryable_anthropic_error",
        lambda exc: isinstance(exc, RetryableTestError),
    )

    result = await client.review_artifact("prompt")

    assert result == "ok"
    assert messages.calls == 3
    assert messages.max_tokens == 1234


def test_factory_passes_anthropic_max_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    created: dict[str, object] = {}

    class FakeAnthropicClient:
        def __init__(self, api_key: str, model: str, max_tokens: int) -> None:
            created["api_key"] = api_key
            created["model"] = model
            created["max_tokens"] = max_tokens

    monkeypatch.setattr(
        factory,
        "settings",
        replace(
            factory.settings,
            llm_provider="anthropic",
            anthropic_api_key="test-key",
            anthropic_model="test-model",
            anthropic_max_tokens=2048,
        ),
    )
    monkeypatch.setattr(factory, "AnthropicClient", FakeAnthropicClient)

    factory.get_llm_client()

    assert created == {
        "api_key": "test-key",
        "model": "test-model",
        "max_tokens": 2048,
    }
