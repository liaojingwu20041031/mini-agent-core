"""Default safe built-in skills."""

from __future__ import annotations

import ast
import datetime as dt
import json
import math
import os
import platform
from typing import Any

from mini_agent.core.tools import tool

_ALLOWED_NAMES = {name: getattr(math, name) for name in dir(math) if not name.startswith("_")}
_ALLOWED_NAMES.update({"abs": abs, "round": round, "min": min, "max": max})


@tool(name="calculator", description="Calculate a simple Python math expression.")
def calculator(expression: str) -> Any:
    tree = ast.parse(expression, mode="eval")
    for node in ast.walk(tree):
        if isinstance(node, (ast.Call, ast.BinOp, ast.UnaryOp, ast.Expression, ast.Load, ast.Constant, ast.Name)):
            continue
        if isinstance(node, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.USub, ast.UAdd)):
            continue
        raise ValueError(f"Unsupported expression element: {type(node).__name__}")
    return eval(compile(tree, "<calculator>", "eval"), {"__builtins__": {}}, _ALLOWED_NAMES)


@tool(description="Convert common units.")
def unit_convert(value: float, from_unit: str, to_unit: str) -> dict[str, float | str]:
    factors = {"m": 1.0, "cm": 0.01, "mm": 0.001, "km": 1000.0, "in": 0.0254, "ft": 0.3048}
    if from_unit not in factors or to_unit not in factors:
        raise ValueError("supported units: m, cm, mm, km, in, ft")
    result = value * factors[from_unit] / factors[to_unit]
    return {"value": result, "unit": to_unit}


@tool(description="Format JSON text with stable indentation.")
def format_json(text: str) -> str:
    return json.dumps(json.loads(text), ensure_ascii=False, indent=2, sort_keys=True)


@tool(description="Summarize short text extractively.")
def summarize_text(text: str, max_sentences: int = 3) -> str:
    parts = [item.strip() for item in text.replace("!", ".").replace("?", ".").split(".") if item.strip()]
    return ". ".join(parts[:max_sentences]) + ("." if parts[:max_sentences] else "")


@tool(description="Extract simple bullet key points from text.")
def extract_key_points(text: str, max_points: int = 5) -> list[str]:
    lines = [line.strip(" -	") for line in text.splitlines() if line.strip()]
    if not lines:
        lines = [part.strip() for part in text.split(".") if part.strip()]
    return lines[:max_points]


@tool(description="Placeholder translation skill for deterministic tests.")
def translate_text(text: str, target_language: str = "zh") -> dict[str, str]:
    return {"target_language": target_language, "text": text}


@tool(description="Create a short task plan from a goal.")
def plan_task(goal: str) -> list[str]:
    return [f"Clarify goal: {goal}", "Identify constraints", "Execute smallest useful step", "Verify result"]


@tool(description="Get the current local time.")
def get_time_local() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


@tool(description="Return basic system status.")
def system_status() -> dict[str, Any]:
    return {"platform": platform.platform(), "python": platform.python_version(), "pid": os.getpid(), "cwd": os.getcwd()}


@tool(description="Read a non-secret config value placeholder.")
def config_get(key: str) -> dict[str, str]:
    return {"key": key, "value": ""}


@tool(description="List built-in tool names.")
def tool_list() -> list[str]:
    return [
        "calculator",
        "unit_convert",
        "format_json",
        "summarize_text",
        "extract_key_points",
        "translate_text",
        "plan_task",
        "get_time_local",
        "system_status",
        "config_get",
        "tool_list",
        "web_search",
        "fetch_url_text",
        "weather_open_meteo",
    ]
