"""LLM client boundary used by Agent Core."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from mini_agent.core.messages import Message, ToolCall


@dataclass
class LLMResponse:
    """A normalized chat-completion response."""

    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: dict | None = None


class LLMClient(Protocol):
    """Protocol implemented by OpenAI-compatible or local model adapters."""

    def chat(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
        timeout: float | None = None,
    ) -> LLMResponse:
        """Return the next assistant response."""

