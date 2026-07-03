"""OpenAI-compatible Chat Completions client."""

from __future__ import annotations

import time
from typing import Any

from mini_agent.adapters.providers import get_provider_preset
from mini_agent.core.errors import AgentError
from mini_agent.core.llm import LLMResponse
from mini_agent.core.messages import Message, ToolCall


class OpenAICompatibleClient:
    """HTTP client for OpenAI-compatible /chat/completions APIs."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float = 30,
        temperature: float = 0.2,
        provider: str = "custom",
        extra_body: dict[str, Any] | None = None,
        tool_choice: str | dict[str, Any] = "auto",
        max_retries: int = 2,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.temperature = temperature
        self.provider = provider
        self.extra_body = extra_body or {}
        self.tool_choice = tool_choice
        self.max_retries = max(0, max_retries)
        self._client: Any = None

    @classmethod
    def from_provider(
        cls,
        provider: str,
        api_key: str,
        model: str | None = None,
        region: str | None = None,
        base_url: str | None = None,
        timeout: float = 30,
        temperature: float = 0.2,
        extra_body: dict[str, Any] | None = None,
        tool_choice: str | dict[str, Any] = "auto",
        max_retries: int = 2,
    ) -> "OpenAICompatibleClient":
        preset = get_provider_preset(provider, region)
        if not model:
            raise ValueError(f"Model is required for provider={preset.name}. Configure main.model explicitly.")
        return cls(
            base_url=base_url or preset.base_url,
            api_key=api_key,
            model=model,
            timeout=timeout,
            temperature=temperature,
            provider=preset.name,
            extra_body=extra_body,
            tool_choice=tool_choice,
            max_retries=max_retries,
        )

    def chat(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
        timeout: float | None = None,
    ) -> LLMResponse:
        try:
            import httpx
        except ImportError as exc:
            raise RuntimeError("Install httpx to use OpenAICompatibleClient.") from exc

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [message.to_openai() for message in messages],
            "temperature": self.temperature,
        }
        payload.update(self.extra_body)
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = self.tool_choice

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        url = f"{self.base_url}/chat/completions"
        try:
            response = self._post_with_retries(httpx, url, headers, payload, timeout or self.timeout)
        except httpx.HTTPStatusError as exc:
            body = exc.response.text[:500]
            raise AgentError(
                f"LLM request failed provider={self.provider} status={exc.response.status_code} "
                f"url={url} body={body}"
            ) from exc
        except httpx.HTTPError as exc:
            raise AgentError(f"LLM request failed provider={self.provider} url={url}: {exc}") from exc

        raw = response.json()
        message = raw["choices"][0]["message"]
        tool_calls = [ToolCall.from_openai(call) for call in message.get("tool_calls") or []]
        return LLMResponse(content=message.get("content") or "", tool_calls=tool_calls, raw=raw)

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "OpenAICompatibleClient":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()

    def _http_client(self, httpx_module: Any) -> Any:
        if self._client is None:
            self._client = httpx_module.Client()
        return self._client

    def _post_with_retries(self, httpx_module: Any, url: str, headers: dict[str, str], payload: dict[str, Any], timeout: float) -> Any:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self._http_client(httpx_module).post(url, headers=headers, json=payload, timeout=timeout)
                response.raise_for_status()
                return response
            except httpx_module.HTTPStatusError as exc:
                last_error = exc
                if exc.response.status_code not in {429, 500, 502, 503, 504} or attempt >= self.max_retries:
                    raise
            except httpx_module.HTTPError as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    raise
            time.sleep(min(0.1 * (2**attempt), 1.0))
        if last_error:
            raise last_error
        raise RuntimeError("LLM request failed without a response")
