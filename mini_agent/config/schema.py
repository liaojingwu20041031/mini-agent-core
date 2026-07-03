"""Dataclasses for profile YAML configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProviderConfig:
    name: str
    base_url: str = ""
    api_key_env: str = ""
    aliases: tuple[str, ...] = ()
    note: str = ""
    example_models: tuple[str, ...] = ()


@dataclass
class ModelRoleConfig:
    role: str
    provider: str = ""
    model: str = ""
    base_url: str = ""
    api_key_env: str = ""
    timeout: float = 30
    temperature: float = 0.2
    extra_body: dict[str, Any] = field(default_factory=dict)
    adapter: str = ""
    binary_path: str = ""
    model_path: str = ""
    model_dir: str = ""
    voice: str = "alloy"


@dataclass
class AgentRuntimeConfig:
    max_steps: int = 5
    max_messages: int | None = None
    tool_result_max_chars: int = 4000
    system_prompt: str = "You are a helpful lightweight AI agent."


@dataclass
class ToolsConfig:
    enabled: tuple[str, ...] | None = None
    toolpacks_enabled: tuple[str, ...] = ()
    extensions: tuple[dict[str, Any], ...] = ()
    allow_danger: bool = False


@dataclass
class AppProfileConfig:
    profile: str
    providers: dict[str, ProviderConfig] = field(default_factory=dict)
    models: dict[str, ModelRoleConfig] = field(default_factory=dict)
    agent: AgentRuntimeConfig = field(default_factory=AgentRuntimeConfig)
    tools: ToolsConfig = field(default_factory=ToolsConfig)
    voice: dict[str, Any] = field(default_factory=dict)
    mcp: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    def role(self, name: str) -> ModelRoleConfig:
        if name not in self.models:
            raise KeyError(f"Missing model role: {name}")
        return self.models[name]
