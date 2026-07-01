"""Configurable Agent identity and instruction assembly."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class AgentSpecConfig:
    name: str
    role: str = ""
    identity: str = ""
    position: str = ""
    capabilities: list[str] = field(default_factory=list)
    boundaries: list[str] = field(default_factory=list)
    style: dict[str, Any] = field(default_factory=dict)
    tool_policy: dict[str, Any] = field(default_factory=dict)
    project_context: str = ""
    extra_instructions: str = ""

    def to_system_prompt(self) -> str:
        parts: list[str] = []
        title = self.name.strip()
        if self.role.strip():
            title = f"{title} / {self.role.strip()}" if title else self.role.strip()
        if title:
            parts.append(f"Agent: {title}")
        if self.identity.strip():
            parts.append(f"Identity: {self.identity.strip()}")
        if self.position.strip():
            parts.append(f"Position: {self.position.strip()}")
        if self.capabilities:
            parts.append("Capabilities:\n" + _bullet_lines(self.capabilities))
        if self.boundaries:
            parts.append("Boundaries:\n" + _bullet_lines(self.boundaries))
        if self.style:
            parts.append("Style:\n" + _dict_lines(self.style))
        if self.tool_policy:
            parts.append("Tool policy:\n" + _dict_lines(self.tool_policy))
        if self.project_context.strip():
            parts.append(f"Project context: {self.project_context.strip()}")
        if self.extra_instructions.strip():
            parts.append(f"Extra instructions: {self.extra_instructions.strip()}")
        return "\n\n".join(parts).strip()


def load_agent_spec(config_dir: str | Path, agent_name: str = "default") -> AgentSpecConfig | None:
    path = Path(config_dir) / "agents.yaml"
    if not path.exists():
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    agents = data.get("agents", data)
    if not isinstance(agents, dict):
        raise ValueError(f"Agent 配置格式错误：{path}")
    raw = agents.get(agent_name)
    if raw is None:
        available = ", ".join(sorted(str(name) for name in agents))
        raise ValueError(f"未知 Agent {agent_name!r}；可选：{available}")
    if not isinstance(raw, dict):
        raise ValueError(f"Agent {agent_name!r} 必须是对象配置")
    return AgentSpecConfig(
        name=str(raw.get("name", agent_name)),
        role=str(raw.get("role", "")),
        identity=str(raw.get("identity", "")),
        position=str(raw.get("position", "")),
        capabilities=list(raw.get("capabilities") or []),
        boundaries=list(raw.get("boundaries") or []),
        style=dict(raw.get("style") or {}),
        tool_policy=dict(raw.get("tool_policy") or {}),
        project_context=str(raw.get("project_context", "")),
        extra_instructions=str(raw.get("extra_instructions", "")),
    )


def _bullet_lines(items: list[str]) -> str:
    return "\n".join(f"- {str(item).strip()}" for item in items if str(item).strip())


def _dict_lines(data: dict[str, Any]) -> str:
    lines = []
    for key, value in data.items():
        if isinstance(value, (list, tuple)):
            rendered = ", ".join(str(item) for item in value)
        else:
            rendered = str(value)
        lines.append(f"- {key}: {rendered}")
    return "\n".join(lines)
