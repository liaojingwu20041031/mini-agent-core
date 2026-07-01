"""Confirm-risk built-in skills."""

from __future__ import annotations

from pathlib import Path

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
