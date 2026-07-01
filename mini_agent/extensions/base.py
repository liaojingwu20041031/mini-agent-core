"""Lightweight extension interfaces for project-specific capabilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from mini_agent.core.tools import ToolRegistry


@dataclass
class ToolPack:
    name: str
    description: str
    tools: list[Callable]
    default_enabled: bool = False

    def register(self, registry: ToolRegistry) -> None:
        registry.register_many(self.tools)


@dataclass
class Capability:
    name: str
    description: str
    toolpacks: list[str]
    agent_instructions: str = ""
    config_patch: dict = field(default_factory=dict)
