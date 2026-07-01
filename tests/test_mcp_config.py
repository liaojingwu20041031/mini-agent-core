from mini_agent.mcp.manager import MCPManager


def test_disabled_mcp_servers_do_not_build_processes():
    manager = MCPManager({"servers": {"shell": {"enabled": False, "risk_level": "danger", "command": "sh"}}})

    assert manager.validate() == []
    assert manager.enabled_servers() == []
    assert manager.build_processes() == []


def test_enabled_filesystem_requires_sandbox():
    manager = MCPManager({"servers": {"filesystem": {"enabled": True, "risk_level": "confirm", "command": "fs-mcp"}}})

    assert any("filesystem MCP requires sandbox" in error for error in manager.validate())
