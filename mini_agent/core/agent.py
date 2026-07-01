"""Synchronous minimal Agent loop."""

from __future__ import annotations

from dataclasses import dataclass

from mini_agent.core.guard import ToolGuard
from mini_agent.core.llm import LLMClient
from mini_agent.core.messages import Message
from mini_agent.core.session import Session
from mini_agent.core.tools import ToolRegistry
from mini_agent.core.trace import trace_span


@dataclass
class Agent:
    """Reusable Agent Core shared by text and voice interactions."""

    llm: LLMClient
    tools: ToolRegistry | None = None
    system_prompt: str | None = "You are a helpful lightweight AI agent."
    max_steps: int = 5
    llm_timeout: float = 30
    tool_timeout: float = 30
    guard: ToolGuard | None = None

    def __post_init__(self) -> None:
        self.tools = self.tools or ToolRegistry()
        self.guard = self.guard or ToolGuard()
        self.session = Session(system_prompt=self.system_prompt)

    def reset(self) -> None:
        self.session.reset()

    def run(self, user_input: str) -> str:
        """Run one user turn until final text or max tool steps."""

        self.session.add(Message(role="user", content=user_input))

        for step in range(self.max_steps + 1):
            with trace_span("llm.chat", detail=f"step={step}"):
                response = self.llm.chat(
                    self.session.to_llm_messages(),
                    tools=self.tools.schemas() if self.tools else None,
                    timeout=self.llm_timeout,
                )

            if not response.tool_calls:
                final = response.content or ""
                self.session.add(Message(role="assistant", content=final))
                return final

            if step >= self.max_steps:
                final = "Agent stopped because max_steps was reached before a final answer."
                self.session.add(Message(role="assistant", content=final))
                return final

            self.session.add(
                Message(
                    role="assistant",
                    content=response.content or "",
                    tool_calls=response.tool_calls,
                )
            )
            for call in response.tool_calls:
                result = self.tools.execute(call, guard=self.guard, default_timeout=self.tool_timeout)
                self.session.add(
                    Message(
                        role="tool",
                        content=result.to_message_content(),
                        name=result.name,
                        tool_call_id=result.tool_call_id,
                    )
                )

        final = "Agent stopped unexpectedly after the tool loop."
        self.session.add(Message(role="assistant", content=final))
        return final

