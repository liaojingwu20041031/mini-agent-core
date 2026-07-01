"""Registries for provider metadata and role model configuration."""

from __future__ import annotations

from dataclasses import dataclass, field

from mini_agent.config.schema import ModelRoleConfig, ProviderConfig


@dataclass
class ProviderRegistry:
    providers: dict[str, ProviderConfig] = field(default_factory=dict)

    def register(self, provider: ProviderConfig) -> None:
        self.providers[provider.name] = provider
        for alias in provider.aliases:
            self.providers[alias] = provider

    def get(self, name: str) -> ProviderConfig:
        if name not in self.providers:
            raise KeyError(f"Unknown provider: {name}")
        return self.providers[name]


@dataclass
class ModelRegistry:
    roles: dict[str, ModelRoleConfig] = field(default_factory=dict)

    def register(self, role: ModelRoleConfig) -> None:
        self.roles[role.role] = role

    def get(self, role: str) -> ModelRoleConfig:
        if role not in self.roles:
            raise KeyError(f"Unknown model role: {role}")
        return self.roles[role]
