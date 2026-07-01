"""Short-lived conversation session state."""

from __future__ import annotations

from dataclasses import dataclass, field

from mini_agent.core.messages import Message


@dataclass
class Session:
    """Stores in-memory conversation history for one Agent."""

    system_prompt: str | None = None
    messages: list[Message] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.messages = []
        if self.system_prompt:
            self.messages.append(Message(role="system", content=self.system_prompt))

    def add(self, message: Message) -> None:
        self.messages.append(message)

    def to_llm_messages(self) -> list[Message]:
        return list(self.messages)

