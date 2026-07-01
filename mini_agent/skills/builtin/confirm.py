"""Confirm-risk built-in skills."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from mini_agent.core.tools import tool


@tool(description="Write text to a named in-memory memory slot.", risk_level="confirm")
def memory_write(key: str, value: str) -> dict[str, str]:
    return {"key": key, "value": value}


@tool(description="Set a mock LED state.", risk_level="confirm")
def set_mock_led(state: str) -> dict[str, str]:
    if state not in {"on", "off", "blink"}:
        raise ValueError("state must be one of: on, off, blink")
    return {"led": state}


@tool(description="Write a file under an explicit sandbox directory.", risk_level="confirm")
def file_write_sandbox(sandbox_dir: str, relative_path: str, content: str) -> dict[str, str]:
    root = Path(sandbox_dir).resolve()
    target = (root / relative_path).resolve()
    if root not in target.parents and target != root:
        raise ValueError("target must stay inside sandbox_dir")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"path": str(target)}


@tool(description="Append text to a file under an explicit sandbox directory.", risk_level="confirm")
def file_append_sandbox(sandbox_dir: str, relative_path: str, content: str) -> dict[str, str]:
    root = Path(sandbox_dir).resolve()
    target = (root / relative_path).resolve()
    if root not in target.parents and target != root:
        raise ValueError("target must stay inside sandbox_dir")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(content)
    return {"path": str(target)}


@tool(description="POST JSON to an HTTP endpoint after explicit confirmation.", risk_level="confirm", timeout=15)
def http_post_json_confirm(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = httpx.post(url, json=payload, timeout=10)
    return {"status_code": response.status_code, "text": response.text[:1000]}


@tool(description="Placeholder ROS2 service call. Replace with project-specific implementation.", risk_level="confirm")
def ros2_call_service_confirm(service_name: str, request: dict[str, Any]) -> dict[str, Any]:
    return {"ok": False, "service_name": service_name, "request": request, "note": "ROS2 stub: implement in an external ToolPack."}


@tool(description="Placeholder ROS2 action goal. Replace with project-specific implementation.", risk_level="confirm")
def ros2_send_goal_confirm(action_name: str, goal: dict[str, Any]) -> dict[str, Any]:
    return {"ok": False, "action_name": action_name, "goal": goal, "note": "ROS2 stub: implement in an external ToolPack."}
