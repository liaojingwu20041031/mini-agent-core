"""Bridge explicitly declared MCP tools into ToolRegistry definitions."""

from __future__ import annotations

from typing import Any

from mini_agent.core.tools import ToolDefinition, ToolRegistry
from mini_agent.mcp.server_config import MCPServerConfig, MCPToolConfig


class MCPToolBridge:
    def __init__(self, servers: list[MCPServerConfig]) -> None:
        self.servers = servers

    def tool_definitions(self) -> list[ToolDefinition]:
        definitions: list[ToolDefinition] = []
        for server in self.servers:
            for tool in server.tools:
                definitions.append(self._definition(server, tool))
        return definitions

    def register(self, registry: ToolRegistry) -> None:
        for definition in self.tool_definitions():
            registry.register(definition)

    def _definition(self, server: MCPServerConfig, tool_cfg: MCPToolConfig) -> ToolDefinition:
        risk = tool_cfg.risk_level or server.risk_level

        def call_mcp_tool(**kwargs: Any) -> dict[str, Any]:
            raise NotImplementedError("MCP tools/list and tools/call are extension points for V0.1.")

        return ToolDefinition(
            name=f"mcp_{server.name}_{tool_cfg.name}",
            description=tool_cfg.description,
            func=call_mcp_tool,
            risk_level=risk,
            parameters={"type": "object", "properties": {}, "additionalProperties": True},
            timeout=server.startup_timeout,
        )
