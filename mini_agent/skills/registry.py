"""Built-in skill registry with explicit risk-tier registration."""

from __future__ import annotations

from collections.abc import Iterable

from mini_agent.core.tools import ToolDefinition, ToolRegistry
from mini_agent.skills.builtin import confirm, danger, safe

SAFE_SKILLS = {
    "calculator": safe.calculator,
    "unit_convert": safe.unit_convert,
    "format_json": safe.format_json,
    "summarize_text": safe.summarize_text,
    "extract_key_points": safe.extract_key_points,
    "translate_text": safe.translate_text,
    "plan_task": safe.plan_task,
    "get_time_local": safe.get_time_local,
    "system_status": safe.system_status,
    "config_get": safe.config_get,
    "tool_list": safe.tool_list,
}
CONFIRM_SKILLS = {
    "memory_write": confirm.memory_write,
    "set_mock_led": confirm.set_mock_led,
    "file_write_sandbox": confirm.file_write_sandbox,
}
DANGER_SKILLS = {
    "dangerous_shell": danger.dangerous_shell,
    "shell_exec": danger.shell_exec,
}
ALL_SKILLS = {**SAFE_SKILLS, **CONFIRM_SKILLS, **DANGER_SKILLS}
DEFAULT_SAFE_SKILLS = tuple(SAFE_SKILLS)


def get_builtin_skill(name: str) -> ToolDefinition:
    if name not in ALL_SKILLS:
        raise KeyError(f"Unknown built-in skill: {name}")
    return getattr(ALL_SKILLS[name], "__mini_agent_tool__")


def build_tool_registry(enabled: Iterable[str] | None = None) -> ToolRegistry:
    registry = ToolRegistry()
    names = tuple(enabled or DEFAULT_SAFE_SKILLS)
    for name in names:
        if name not in ALL_SKILLS:
            raise KeyError(f"Unknown built-in skill: {name}")
        registry.register(ALL_SKILLS[name])
    return registry
