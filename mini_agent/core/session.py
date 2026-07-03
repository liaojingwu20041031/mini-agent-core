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
        if _has_pending_tool_calls(self.messages):
            return
        system = self.messages[0] if self.messages and self.messages[0].role == "system" else None
        body = self.messages[1:] if system else list(self.messages)
        groups = _message_groups(body)
        keep = max(self.max_messages - (1 if system else 0), 0)

        kept: list[Message] = []
        for group in reversed(groups):
            if kept and len(kept) + len(group) > keep:
                break
            if not kept and len(group) > keep:
                kept = list(group)
                break
            kept = [*group, *kept]
        self.messages = ([system] if system else []) + kept


def _message_groups(messages: list[Message]) -> list[list[Message]]:
    groups: list[list[Message]] = []
    index = 0
    while index < len(messages):
        message = messages[index]
        if message.role == "tool":
            index += 1
            continue
        if message.role == "assistant" and message.tool_calls:
            call_ids = {call.id for call in message.tool_calls}
            group = [message]
            next_index = index + 1
            while next_index < len(messages) and messages[next_index].role == "tool":
                if messages[next_index].tool_call_id in call_ids:
                    group.append(messages[next_index])
                next_index += 1
            if {item.tool_call_id for item in group[1:]} == call_ids:
                groups.append(group)
            index = next_index
            continue
        groups.append([message])
        index += 1
    return groups


def _has_pending_tool_calls(messages: list[Message]) -> bool:
    for index in range(len(messages) - 1, -1, -1):
        message = messages[index]
        if message.role == "assistant" and message.tool_calls:
            call_ids = {call.id for call in message.tool_calls}
            seen = {item.tool_call_id for item in messages[index + 1 :] if item.role == "tool"}
            return not call_ids.issubset(seen)
        if message.role not in {"tool", "assistant"}:
            return False
    return False

