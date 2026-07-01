"""Web ToolPack factory."""

from __future__ import annotations

from mini_agent.extensions.base import ToolPack
from mini_agent.skills.builtin import weather, web


def build_web_toolpack() -> ToolPack:
    return ToolPack(
        name="builtin.web",
        description="公开搜索、公开网页文本抓取和天气查询。",
        tools=[web.web_search, web.fetch_url_text_public, weather.weather_open_meteo],
    )
