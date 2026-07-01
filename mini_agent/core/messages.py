"""Message and tool-call data structures shared by text and voice modes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    """A normalized LLM tool call."""

    id: str
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_openai(cls, raw: dict[str, Any]) -> "ToolCall":
        function = raw.get("function", {})
        arguments = function.get("arguments") or {}
        if isinstance(arguments, str):
            import json

            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {"_raw": arguments}
        return cls(
            id=str(raw.get("id") or function.get("name") or "tool_call"),
            name=str(function.get("name") or raw.get("name") or ""),
            arguments=arguments,
        )

    def to_openai(self) -> dict[str, Any]:
        import json

        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": json.dumps(self.arguments, ensure_ascii=False),
            },
        }


@dataclass
class ToolResult:
    """Structured result returned by a tool execution."""

    tool_call_id: str
    name: str
    content: Any = None
    is_error: bool = False
    error: str | None = None

    def to_message_content(self) -> str:
        import json

        payload = {
            "name": self.name,
            "content": self.content,
            "is_error": self.is_error,
            "error": self.error,
        }
        return json.dumps(payload, ensure_ascii=False, default=str)


@dataclass
class Message:
    """Chat message stored in a session."""

    role: str
    content: str | None = ""
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)

    def to_openai(self) -> dict[str, Any]:
        data: dict[str, Any] = {"role": self.role, "content": self.content or ""}
        if self.name:
            data["name"] = self.name
        if self.tool_call_id:
            data["tool_call_id"] = self.tool_call_id
        if self.tool_calls:
            data["tool_calls"] = [call.to_openai() for call in self.tool_calls]
        return data

