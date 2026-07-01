from mini_agent.builtin_tools import register_builtin_tools
from mini_agent.core.tools import ToolRegistry


def test_dangerous_shell_not_default():
    registry = ToolRegistry()
    register_builtin_tools(registry)

    assert registry.get("dangerous_shell") is None
