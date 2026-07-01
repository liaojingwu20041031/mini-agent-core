"""OpenAI-compatible Chat Completions client."""

from __future__ import annotations

from typing import Any

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
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.temperature = temperature

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
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=timeout or self.timeout,
        )
        response.raise_for_status()
        raw = response.json()
        message = raw["choices"][0]["message"]
        tool_calls = [ToolCall.from_openai(call) for call in message.get("tool_calls") or []]
        return LLMResponse(content=message.get("content") or "", tool_calls=tool_calls, raw=raw)

