from mini_agent.core.messages import ToolCall
from mini_agent.core.tools import ToolRegistry, tool


@tool
def broken():
    raise RuntimeError("boom")


def test_tool_exception_is_structured_error():
    registry = ToolRegistry()
    registry.register(broken)

    result = registry.execute(ToolCall(id="1", name="broken"))
    assert result.is_error
    assert "RuntimeError: boom" in result.error
    assert "traceback" in result.content

