"""Project ToolPack placeholder helpers."""

from __future__ import annotations

from mini_agent.extensions.base import ToolPack


def empty_project_toolpack(name: str = "project.empty") -> ToolPack:
    return ToolPack(name=name, description="Project extension placeholder.", tools=[])
