from mini_agent.builtin_tools import register_builtin_tools
from mini_agent.core.tools import ToolRegistry
from mini_agent.skills.registry import build_tool_registry


def test_default_skills_are_safe_only():
    registry = build_tool_registry()
    names = {tool.name for tool in registry.list()}

    assert "calculator" in names
    assert "dangerous_shell" not in names
    assert all(tool.risk_level == "safe" for tool in registry.list())


def test_confirm_and_danger_require_explicit_enable():
    registry = build_tool_registry(["set_mock_led", "dangerous_shell"])
    risks = {tool.name: tool.risk_level for tool in registry.list()}

    assert risks["set_mock_led"] == "confirm"
    assert risks["dangerous_shell"] == "danger"


def test_legacy_builtin_registration_omits_dangerous_shell():
    registry = ToolRegistry()
    register_builtin_tools(registry)
    names = {tool.name for tool in registry.list()}

    assert "dangerous_shell" not in names
