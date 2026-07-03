"""MCP manager that validates config and constructs process wrappers on demand."""

from __future__ import annotations

from pathlib import Path

from mini_agent.mcp.process import MCPProcess
from mini_agent.mcp.server_config import MCPServerConfig

DANGEROUS_DEFAULT_DISABLED = {"playwright", "shell", "docker", "email", "calendar", "database_write"}


class MCPManager:
    def __init__(self, profile_config: dict) -> None:
        raw_servers = profile_config.get("servers", profile_config) if profile_config else {}
        self.servers = {name: MCPServerConfig.from_dict(name, data or {}) for name, data in raw_servers.items()}

    def validate(self) -> list[str]:
        errors: list[str] = []
        for server in self.servers.values():
            if not server.enabled:
                continue
            if server.name in DANGEROUS_DEFAULT_DISABLED and server.risk_level != "safe":
                errors.append(f"MCP server {server.name} must be explicitly reviewed before enabling")
            if server.risk_level not in {"safe", "confirm", "danger"}:
                errors.append(f"MCP server {server.name} has invalid risk_level {server.risk_level!r}")
            if server.name == "filesystem":
                if not server.sandbox:
                    errors.append("filesystem MCP requires sandbox")
                elif not Path(server.sandbox).exists():
                    errors.append(f"filesystem MCP sandbox does not exist: {server.sandbox}")
            if server.enabled and server.transport == "stdio" and not server.command:
                errors.append(f"MCP server {server.name} enabled without command")
            if server.tools:
                errors.append(f"MCP server {server.name} declares tools, but MCP tools/call is not implemented in V0.1")
        return errors

    def enabled_servers(self) -> list[MCPServerConfig]:
        return [server for server in self.servers.values() if server.enabled]

    def build_processes(self) -> list[MCPProcess]:
        return [MCPProcess(server) for server in self.enabled_servers()]
