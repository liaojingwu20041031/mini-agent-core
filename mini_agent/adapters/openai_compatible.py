"""OpenAI-compatible Chat Completions client."""

from __future__ import annotations

from typing import Any

from mini_agent.adapters.providers import get_provider_preset
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
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.temperature = temperature
        self.provider = provider
        self.extra_body = extra_body or {}

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
    ) -> "OpenAICompatibleClient":
        preset = get_provider_preset(provider, region)
        return cls(
            base_url=base_url or preset.base_url,
            api_key=api_key,
            model=model or preset.default_model,
            timeout=timeout,
            temperature=temperature,
            provider=preset.name,
            extra_body=extra_body,
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
            payload["tool_choice"] = "auto"

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        url = f"{self.base_url}/chat/completions"
        try:
            response = httpx.post(
                url,
                headers=headers,
                json=payload,
                timeout=timeout or self.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            body = exc.response.text[:500]
            raise RuntimeError(
                f"LLM request failed provider={self.provider} status={exc.response.status_code} "
                f"url={url} body={body}"
            ) from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"LLM request failed provider={self.provider} url={url}: {exc}") from exc

        raw = response.json()
        message = raw["choices"][0]["message"]
        tool_calls = [ToolCall.from_openai(call) for call in message.get("tool_calls") or []]
        return LLMResponse(content=message.get("content") or "", tool_calls=tool_calls, raw=raw)
