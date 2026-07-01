"""Generic mock tools for demos and tests."""

from __future__ import annotations

import ast
import datetime as dt
import math
import os
import platform
import subprocess
from typing import Any

from mini_agent.core.tools import tool


@tool(description="Get the current local time.")
def get_time() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


_ALLOWED_NAMES = {name: getattr(math, name) for name in dir(math) if not name.startswith("_")}
_ALLOWED_NAMES.update({"abs": abs, "round": round, "min": min, "max": max})


@tool(description="Calculate a simple Python math expression.")
def calculate(expression: str) -> Any:
    tree = ast.parse(expression, mode="eval")
    for node in ast.walk(tree):
        if isinstance(node, (ast.Call, ast.BinOp, ast.UnaryOp, ast.Expression, ast.Load, ast.Constant, ast.Name)):
            continue
        if isinstance(node, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.USub, ast.UAdd)):
            continue
        raise ValueError(f"Unsupported expression element: {type(node).__name__}")
    return eval(compile(tree, "<calculate>", "eval"), {"__builtins__": {}}, _ALLOWED_NAMES)


@tool(description="Return basic system status.")
def get_system_status() -> dict[str, Any]:
    return {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "pid": os.getpid(),
        "cwd": os.getcwd(),
    }


@tool(description="Read a mock sensor value.")
def read_mock_sensor(sensor_name: str) -> dict[str, Any]:
    values = {"temperature": 24.5, "humidity": 52.0, "distance": 1.25}
    return {"sensor": sensor_name, "value": values.get(sensor_name, 0.0)}


@tool(description="Set a mock LED state.", risk_level="confirm")
def set_mock_led(state: str) -> dict[str, str]:
    if state not in {"on", "off", "blink"}:
        raise ValueError("state must be one of: on, off, blink")
    return {"led": state}


@tool(description="Run a shell command. Disabled by default.", risk_level="danger", timeout=5)
def dangerous_shell(command: str) -> dict[str, Any]:
    completed = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=5)
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def register_builtin_tools(registry) -> None:
    registry.register_many(
        [
            get_time,
            calculate,
            get_system_status,
            read_mock_sensor,
            set_mock_led,
            dangerous_shell,
        ]
    )

