from mini_agent.config.loader import load_profile_config
from mini_agent.skills.registry import build_tool_registry


def _names(profile: str) -> set[str]:
    config = load_profile_config("config", profile)
    return {tool.name for tool in build_tool_registry(config.tools.enabled).list()}


def test_standard_profiles_default_online_safe_tools():
    for profile in ["local", "qwen", "deepseek", "kimi", "glm", "siliconflow", "remote"]:
        names = _names(profile)
        assert "web_search" in names
        assert "weather_open_meteo" in names
        assert "dangerous_shell" not in names


def test_minimal_and_online_tool_profiles():
    assert "web_search" not in _names("minimal")
    online = _names("online")
    assert {"web_search", "fetch_url_text", "weather_open_meteo"}.issubset(online)
    assert "dangerous_shell" not in online
