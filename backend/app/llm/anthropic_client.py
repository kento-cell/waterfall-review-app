from __future__ import annotations

from tenacity import AsyncRetrying, retry_if_exception, stop_after_attempt, wait_exponential


class AnthropicClient:
    def __init__(self, api_key: str, model: str, max_tokens: int) -> None:
        if not api_key or api_key == "xxx":
            raise RuntimeError("ANTHROPIC_API_KEY is not configured")
        try:
            from anthropic import AsyncAnthropic
        except ImportError as exc:
            raise RuntimeError("anthropic package is not installed") from exc

        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    async def review_artifact(self, prompt: str) -> str:
        async for attempt in AsyncRetrying(
            retry=retry_if_exception(_is_retryable_anthropic_error),
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=0.01, min=0.01, max=0.05),
            reraise=True,
        ):
            with attempt:
                response = await self._client.messages.create(
                    model=self._model,
                    max_tokens=self._max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                )
        texts: list[str] = []
        for block in response.content:
            if getattr(block, "type", None) == "text":
                texts.append(block.text)
        return "\n".join(texts)


def _is_retryable_anthropic_error(exc: BaseException) -> bool:
    try:
        from anthropic import APIConnectionError, APIError, APIStatusError, RateLimitError
    except ImportError:
        return False

    if isinstance(exc, (APIConnectionError, RateLimitError)):
        return True
    if isinstance(exc, APIStatusError):
        return getattr(exc, "status_code", 0) >= 500
    return isinstance(exc, APIError)
