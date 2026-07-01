"""Built-in ToolPack definitions."""

from __future__ import annotations

from mini_agent.extensions.base import ToolPack
from mini_agent.skills.builtin import confirm, safe, weather, web


def builtin_toolpacks() -> dict[str, ToolPack]:
    return {
        "builtin.basic": ToolPack(
            name="builtin.basic",
            description="基础计算、时间、系统状态和工具列表。",
            tools=[safe.calculator, safe.unit_convert, safe.get_time_local, safe.system_status, safe.tool_list],
            default_enabled=True,
        ),
        "builtin.text": ToolPack(
            name="builtin.text",
            description="文本格式化、摘要、要点提取、翻译占位和计划生成。",
            tools=[safe.format_json, safe.summarize_text, safe.extract_key_points, safe.translate_text, safe.plan_task],
            default_enabled=True,
        ),
        "builtin.web": ToolPack(
            name="builtin.web",
            description="公开 Web 搜索和公开 URL 文本抓取。",
            tools=[web.web_search, web.fetch_url_text_public],
            default_enabled=True,
        ),
        "builtin.weather": ToolPack(
            name="builtin.weather",
            description="Open-Meteo 天气查询。",
            tools=[weather.weather_open_meteo],
            default_enabled=True,
        ),
        "builtin.system": ToolPack(
            name="builtin.system",
            description="低风险本机状态与非敏感配置读取占位。",
            tools=[safe.system_status, safe.config_get, safe.tool_list],
            default_enabled=True,
        ),
        "builtin.memory": ToolPack(
            name="builtin.memory",
            description="需要确认的记忆和沙箱写入工具。",
            tools=[confirm.memory_write, confirm.file_write_sandbox, confirm.file_append_sandbox],
            default_enabled=False,
        ),
    }
