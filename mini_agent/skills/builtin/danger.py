"""Danger-risk built-in skills, never registered by default."""

from __future__ import annotations

import subprocess
from typing import Any

from mini_agent.core.tools import tool

MAX_SHELL_OUTPUT_CHARS = 4000


@tool(description="Run a shell command. Disabled by default.", risk_level="danger", timeout=5)
def dangerous_shell(command: str) -> dict[str, Any]:
    completed = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=5)
    stdout, stdout_truncated = _limit_output(completed.stdout)
    stderr, stderr_truncated = _limit_output(completed.stderr)
    return {
        "returncode": completed.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "stdout_truncated": stdout_truncated,
        "stderr_truncated": stderr_truncated,
    }


@tool(description="Run a shell command. Disabled by default.", risk_level="danger", timeout=5)
def shell_exec(command: str) -> dict[str, Any]:
    return dangerous_shell(command)


def _limit_output(text: str) -> tuple[str, bool]:
    if len(text) <= MAX_SHELL_OUTPUT_CHARS:
        return text, False
    return text[:MAX_SHELL_OUTPUT_CHARS] + "...[truncated]", True
