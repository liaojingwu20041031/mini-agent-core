"""Tool permission guardrails."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


ConfirmCallback = Callable[[str, dict[str, Any]], bool]


@dataclass
class ToolGuard:
    """Applies safe/confirm/danger policy before tool execution."""

    confirm_callback: ConfirmCallback | None = None
    allow_danger: bool = False

    def check(self, name: str, risk_level: str, arguments: dict[str, Any]) -> tuple[bool, str | None]:
        if risk_level == "safe":
            return True, None
        if risk_level == "confirm":
            if not self.confirm_callback:
                return False, "Tool requires confirmation but no confirm_callback was provided."
            if self.confirm_callback(name, arguments):
                return True, None
            return False, "Tool execution was rejected by confirm_callback."
        if risk_level == "danger":
            if self.allow_danger:
                return True, None
            return False, "Dangerous tools are disabled. Set allow_danger=True to enable."
        return False, f"Unknown risk_level: {risk_level}"

