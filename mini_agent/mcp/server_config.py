"""MCP server configuration dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MCPToolConfig:
    name: str
    description: str = "MCP tool placeholder"
    risk_level: str = "safe"


@dataclass
class MCPServerConfig:
    name: str
    enabled: bool = False
    transport: str = "stdio"
    command: str = ""
    args: tuple[str, ...] = ()
    env: dict[str, str] = field(default_factory=dict)
    risk_level: str = "safe"
    startup_timeout: float = 10
    sandbox: str = ""
    tools: tuple[MCPToolConfig, ...] = ()

    @classmethod
    def from_dict(cls, name: str, data: dict) -> "MCPServerConfig":
        tools = tuple(MCPToolConfig(**item) for item in (data.get("tools") or ()))
        return cls(
            name=name,
            enabled=bool(data.get("enabled", False)),
            transport=str(data.get("transport", "stdio")),
            command=str(data.get("command", "")),
            args=tuple(data.get("args") or ()),
            env=dict(data.get("env") or {}),
            risk_level=str(data.get("risk_level", "safe")),
            startup_timeout=float(data.get("startup_timeout", 10)),
            sandbox=str(data.get("sandbox", "")),
            tools=tools,
        )
