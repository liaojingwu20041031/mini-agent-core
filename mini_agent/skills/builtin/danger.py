"""Danger-risk built-in skills, never registered by default."""

from __future__ import annotations

import subprocess
from typing import Any

from mini_agent.core.tools import tool


@tool(description="Run a shell command. Disabled by default.", risk_level="danger", timeout=5)
def dangerous_shell(command: str) -> dict[str, Any]:
    completed = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=5)
    return {"returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}


@tool(description="Run a shell command. Disabled by default.", risk_level="danger", timeout=5)
def shell_exec(command: str) -> dict[str, Any]:
    return dangerous_shell(command)
