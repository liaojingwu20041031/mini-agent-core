"""Load nested YAML profile configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from mini_agent.adapters.providers import list_provider_presets
from mini_agent.config.schema import (
    AgentRuntimeConfig,
    AppProfileConfig,
    ModelRoleConfig,
    ProviderConfig,
    ToolsConfig,
)

CONFIG_FILES = ("providers", "models", "agent", "voice", "tools", "mcp")


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        example = path.with_suffix(path.suffix + ".example")
        raise FileNotFoundError(f"Missing config file: {path}. Copy from {example} and edit it.")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data or {}


def _profile_section(data: dict[str, Any], profile: str) -> dict[str, Any]:
    profiles = data.get("profiles")
    if not isinstance(profiles, dict):
        return data
    section = profiles.get(profile)
    if section is None:
        available = ", ".join(sorted(profiles))
        raise ValueError(f"Unknown profile {profile!r}. Available profiles: {available}")
    return section or {}


def _provider_configs(raw: dict[str, Any]) -> dict[str, ProviderConfig]:
    providers = {
        preset.name: ProviderConfig(
            name=preset.name,
            base_url=preset.base_url,
            api_key_env=preset.api_key_env,
            aliases=preset.aliases,
            note=preset.note,
            example_models=preset.example_models,
        )
        for preset in list_provider_presets()
    }
    for name, item in (raw.get("providers") or {}).items():
        if not isinstance(item, dict):
            continue
        base = providers.get(name)
        providers[name] = ProviderConfig(
            name=name,
            base_url=str(item.get("base_url", base.base_url if base else "")),
            api_key_env=str(item.get("api_key_env", base.api_key_env if base else "")),
            aliases=tuple(item.get("aliases", base.aliases if base else ()) or ()),
            note=str(item.get("note", base.note if base else "")),
            example_models=tuple(item.get("example_models", base.example_models if base else ()) or ()),
        )
    return providers


def _role_config(role: str, item: dict[str, Any]) -> ModelRoleConfig:
    return ModelRoleConfig(
        role=role,
        provider=str(item.get("provider", item.get("adapter", ""))),
        model=str(item.get("model", "")),
        base_url=str(item.get("base_url", "")),
        api_key_env=str(item.get("api_key_env", "")),
        timeout=float(item.get("timeout", 30)),
        temperature=float(item.get("temperature", 0.2)),
        extra_body=dict(item.get("extra_body") or {}),
        adapter=str(item.get("adapter", "")),
        binary_path=str(item.get("binary_path", "")),
        model_path=str(item.get("model_path", "")),
        model_dir=str(item.get("model_dir", "")),
        voice=str(item.get("voice", "alloy")),
    )


def load_profile_config(config_dir: str | Path = "config", profile: str = "local") -> AppProfileConfig:
    root = Path(config_dir)
    merged: dict[str, Any] = {}
    for name in CONFIG_FILES:
        path = root / f"{name}.yaml"
        data = _profile_section(_read_yaml(path), profile)
        merged[name] = data

    providers = _provider_configs(merged["providers"])
    models_raw = merged["models"].get("roles", merged["models"])
    models = {role: _role_config(role, item or {}) for role, item in models_raw.items()}
    agent_raw = merged["agent"]
    tools_raw = merged["tools"]
    return AppProfileConfig(
        profile=profile,
        providers=providers,
        models=models,
        agent=AgentRuntimeConfig(
            max_steps=int(agent_raw.get("max_steps", 5)),
            max_messages=agent_raw.get("max_messages"),
            tool_result_max_chars=int(agent_raw.get("tool_result_max_chars", 4000)),
            system_prompt=str(agent_raw.get("system_prompt", "You are a helpful lightweight AI agent.")),
        ),
        tools=ToolsConfig(
            enabled=tuple(tools_raw.get("enabled", ()) or ()),
            allow_danger=bool(tools_raw.get("allow_danger", False)),
        ),
        voice=merged["voice"],
        mcp=merged["mcp"],
        raw=merged,
    )
