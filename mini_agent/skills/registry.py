"""Built-in skill registry with explicit risk-tier registration."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from mini_agent.config.schema import ToolsConfig
from mini_agent.core.tools import ToolDefinition, ToolRegistry
from mini_agent.extensions.loader import load_external_toolpack
from mini_agent.skills.builtin import confirm, danger, safe, weather, web
from mini_agent.toolpacks.builtin import builtin_toolpacks

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
    "web_search": web.web_search,
    "fetch_url_text": web.fetch_url_text,
    "fetch_url_text_public": web.fetch_url_text_public,
    "weather_open_meteo": weather.weather_open_meteo,
}
CONFIRM_SKILLS = {
    "memory_write": confirm.memory_write,
    "set_mock_led": confirm.set_mock_led,
    "file_write_sandbox": confirm.file_write_sandbox,
    "file_append_sandbox": confirm.file_append_sandbox,
    "http_post_json_confirm": confirm.http_post_json_confirm,
    "ros2_call_service_confirm": confirm.ros2_call_service_confirm,
    "ros2_send_goal_confirm": confirm.ros2_send_goal_confirm,
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


def build_tool_registry(enabled: Iterable[str] | ToolsConfig | None = None) -> ToolRegistry:
    registry = ToolRegistry()
    toolpacks_enabled: tuple[str, ...] = ()
    extensions: tuple[dict[str, Any], ...] = ()
    if isinstance(enabled, ToolsConfig):
        names = tuple(enabled.enabled or ())
        toolpacks_enabled = tuple(enabled.toolpacks_enabled or ())
        extensions = tuple(enabled.extensions or ())
    else:
        names = tuple(enabled or DEFAULT_SAFE_SKILLS)
    packs = builtin_toolpacks()
    for pack_name in toolpacks_enabled:
        if pack_name not in packs:
            raise KeyError(f"Unknown ToolPack: {pack_name}")
        packs[pack_name].register(registry)
    for extension in extensions:
        try:
            load_external_toolpack(extension).register(registry)
        except Exception as exc:
            print(f"外部 ToolPack 加载失败：{exc}")
    for name in names:
        if name not in ALL_SKILLS:
            raise KeyError(f"Unknown built-in skill: {name}")
        registry.register(ALL_SKILLS[name])
    if not toolpacks_enabled and not names:
        for name in DEFAULT_SAFE_SKILLS:
            registry.register(ALL_SKILLS[name])
    return registry
