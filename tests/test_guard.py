from mini_agent.core.guard import ToolGuard
from mini_agent.core.messages import ToolCall
from mini_agent.core.tools import ToolRegistry, tool


@tool
def safe_value():
    return "ok"


@tool(risk_level="confirm")
def confirm_value():
    return "confirmed"


@tool(risk_level="danger")
def danger_value():
    return "danger"


def test_safe_tool_executes():
    registry = ToolRegistry()
    registry.register(safe_value)
    result = registry.execute(ToolCall(id="1", name="safe_value"))
    assert not result.is_error
    assert result.content == "ok"


def test_confirm_tool_without_callback_is_blocked():
    registry = ToolRegistry()
    registry.register(confirm_value)
    result = registry.execute(ToolCall(id="1", name="confirm_value"))
    assert result.is_error
    assert "confirmation" in result.error


def test_confirm_tool_with_callback_executes():
    registry = ToolRegistry()
    registry.register(confirm_value)
    guard = ToolGuard(confirm_callback=lambda name, args: True)
    result = registry.execute(ToolCall(id="1", name="confirm_value"), guard=guard)
    assert not result.is_error
    assert result.content == "confirmed"


def test_danger_tool_default_blocked():
    registry = ToolRegistry()
    registry.register(danger_value)
    result = registry.execute(ToolCall(id="1", name="danger_value"))
    assert result.is_error
    assert "Dangerous tools are disabled" in result.error


def test_danger_tool_allowed_explicitly():
    registry = ToolRegistry()
    registry.register(danger_value)
    result = registry.execute(ToolCall(id="1", name="danger_value"), guard=ToolGuard(allow_danger=True))
    assert not result.is_error
    assert result.content == "danger"

