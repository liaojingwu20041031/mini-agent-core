"""Reserved MCP adapter boundary."""

from __future__ import annotations

from typing import Any

from mini_agent.core.tools import ToolDefinition


class MCPAdapter:
    """Future adapter that can expose MCP tools as mini_agent ToolDefinition objects."""

    def list_tools(self) -> list[ToolDefinition]:
        raise NotImplementedError("TODO V0.2: map MCP tool metadata to ToolDefinition.")

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        raise NotImplementedError("TODO V0.2: call an MCP server tool.")

