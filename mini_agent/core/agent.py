"""Synchronous minimal Agent loop."""

from __future__ import annotations

from dataclasses import dataclass
import time

from mini_agent.core.errors import AgentError
from mini_agent.core.guard import ToolGuard
from mini_agent.core.llm import LLMClient
from mini_agent.core.messages import Message
from mini_agent.core.session import Session
from mini_agent.core.status import NullStatusSink, StatusEvent, StatusSink
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
    session_max_messages: int | None = None
    tool_result_max_chars: int = 4000
    status_sink: StatusSink | None = None

    def __post_init__(self) -> None:
        self.tools = self.tools or ToolRegistry()
        self.guard = self.guard or ToolGuard()
        self.status_sink = self.status_sink or NullStatusSink()
        self.session = Session(system_prompt=self.system_prompt, max_messages=self.session_max_messages)

    def reset(self) -> None:
        self.session.reset()

    def run(self, user_input: str) -> str:
        """Run one user turn until final text or max tool steps."""

        if not user_input or not user_input.strip():
            return "Please provide a non-empty user input."
        self._emit("agent", "agent", "start")
        self.session.add(Message(role="user", content=user_input))

        for step in range(self.max_steps + 1):
            llm_started = time.perf_counter()
            self._emit("llm", "chat", "start", detail=f"step={step}")
            with trace_span("llm.chat", detail=f"step={step}"):
                try:
                    response = self.llm.chat(
                        self.session.to_llm_messages(),
                        tools=self.tools.schemas() if self.tools else None,
                        timeout=self.llm_timeout,
                    )
                except AgentError:
                    self._emit("error", "llm", "error", detail="LLM request failed", ok=False)
                    raise
                except Exception as exc:
                    self._emit("error", "llm", "error", detail=f"{type(exc).__name__}: {exc}", ok=False)
                    raise AgentError(f"LLM request failed: {type(exc).__name__}: {exc}") from exc
            self._emit("llm", "chat", "end", detail=f"step={step}", elapsed_ms=_elapsed_ms(llm_started))

            if not response.tool_calls:
                final = response.content or ""
                self.session.add(Message(role="assistant", content=final))
                self._emit("agent", "agent", "end", ok=True)
                return final

            if step >= self.max_steps:
                final = "Agent stopped because max_steps was reached before a final answer."
                self.session.add(Message(role="assistant", content=final))
                self._emit("agent", "agent", "end", detail="max_steps reached", ok=False)
                return final

            self.session.add(
                Message(
                    role="assistant",
                    content=response.content or "",
                    tool_calls=response.tool_calls,
                )
            )
            for call in response.tool_calls:
                tool_started = time.perf_counter()
                self._emit("tool", call.name, "start")
                result = self.tools.execute(call, guard=self.guard, default_timeout=self.tool_timeout)
                elapsed_ms = _elapsed_ms(tool_started)
                self._emit(
                    "tool",
                    result.name,
                    "end",
                    detail=result.error or "",
                    elapsed_ms=elapsed_ms,
                    ok=not result.is_error,
                )
                if result.is_error:
                    self._emit("error", result.name, "error", detail=result.error or "tool error", ok=False)
                self.session.add(
                    Message(
                        role="tool",
                        content=self._truncate_tool_result(result.to_message_content()),
                        name=result.name,
                        tool_call_id=result.tool_call_id,
                    )
                )

        final = "Agent stopped unexpectedly after the tool loop."
        self.session.add(Message(role="assistant", content=final))
        self._emit("agent", "agent", "end", detail="unexpected stop", ok=False)
        return final

    def _truncate_tool_result(self, content: str) -> str:
        if self.tool_result_max_chars <= 0 or len(content) <= self.tool_result_max_chars:
            return content
        return content[: self.tool_result_max_chars] + "...[truncated]"

    def _emit(
        self,
        event_type: str,
        name: str,
        phase: str,
        detail: str = "",
        elapsed_ms: float | None = None,
        ok: bool = True,
    ) -> None:
        self.status_sink.emit(StatusEvent(type=event_type, name=name, phase=phase, detail=detail, elapsed_ms=elapsed_ms, ok=ok))


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 1)

