"""Lightweight status events for CLI and embedders."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class StatusEvent:
    type: str
    name: str
    phase: str
    detail: str = ""
    elapsed_ms: float | None = None
    ok: bool = True


class StatusSink(Protocol):
    def emit(self, event: StatusEvent) -> None:
        """Receive one status event."""


class NullStatusSink:
    def emit(self, event: StatusEvent) -> None:
        return None


class ConsoleStatusSink:
    def emit(self, event: StatusEvent) -> None:
        if event.type == "llm" and event.phase == "start":
            print("[llm] 请求中...")
            return
        if event.type == "llm" and event.phase == "end":
            elapsed = f" {event.elapsed_ms:.0f}ms" if event.elapsed_ms is not None else ""
            print(f"[llm] 完成{elapsed}")
            return
        if event.type == "tool" and event.phase == "start":
            print(f"[tool] {event.name} 开始")
            return
        if event.type == "tool" and event.phase == "end":
            elapsed = f" {event.elapsed_ms:.0f}ms" if event.elapsed_ms is not None else ""
            suffix = "完成" if event.ok else "失败"
            print(f"[tool] {event.name} {suffix}{elapsed}")
            return
        if event.type == "error":
            print(f"[error] {event.name} {event.detail}".strip())


class ListStatusSink:
    def __init__(self) -> None:
        self.events: list[StatusEvent] = []

    def emit(self, event: StatusEvent) -> None:
        self.events.append(event)


class CallbackStatusSink:
    def __init__(self, callback: Callable[[StatusEvent], Any]) -> None:
        self.callback = callback

    def emit(self, event: StatusEvent) -> None:
        self.callback(event)
