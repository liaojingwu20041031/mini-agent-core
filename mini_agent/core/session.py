"""Short-lived conversation session state."""

from __future__ import annotations

from dataclasses import dataclass, field

from mini_agent.core.messages import Message


@dataclass
class Session:
    """Stores in-memory conversation history for one Agent."""

    system_prompt: str | None = None
    max_messages: int | None = None
    max_tokens: int | None = None
    messages: list[Message] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.messages = []
        if self.system_prompt:
            self.messages.append(Message(role="system", content=self.system_prompt))

    def add(self, message: Message) -> None:
        self.messages.append(message)
        self._trim_messages()

    def to_llm_messages(self) -> list[Message]:
        return list(self.messages)

    def _trim_messages(self) -> None:
        if not self.max_messages or len(self.messages) <= self.max_messages:
            return
        if self.messages and self.messages[0].role == "system":
            keep = max(self.max_messages - 1, 0)
            self.messages = [self.messages[0], *self.messages[-keep:]]
        else:
            self.messages = self.messages[-self.max_messages :]

