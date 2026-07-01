"""Validation for profile configuration."""

from __future__ import annotations

from pathlib import Path

from mini_agent.config.env import env_status
from mini_agent.config.schema import AppProfileConfig, ModelRoleConfig

REQUIRED_ROLES = ("main",)
VALID_ROLES = {"main", "stt", "tts", "embedding", "small"}
LOCAL_ADAPTERS = {"whisper_cpp", "sherpa_onnx", "piper"}


def _validate_role(config: AppProfileConfig, role: ModelRoleConfig) -> list[str]:
    errors: list[str] = []
    if role.role not in VALID_ROLES:
        errors.append(f"unknown model role {role.role!r}; expected one of {sorted(VALID_ROLES)}")
    if role.role == "main" and not role.model.strip():
        errors.append("main.model is required; provider presets only list example_models")
    provider_name = role.provider
    if provider_name and provider_name not in config.providers and role.role == "main":
        errors.append(f"main.provider {provider_name!r} is not configured")
    provider = config.providers.get(provider_name)
    base_url = role.base_url or (provider.base_url if provider else "")
    if role.role == "main" and not base_url:
        errors.append("main.base_url is required, either in the role or provider config")
    api_key_env = role.api_key_env or (provider.api_key_env if provider else "")
    if role.role == "main" and api_key_env and not env_status(api_key_env)["present"]:
        errors.append(f"environment variable {api_key_env} is not set for main provider")
    if role.timeout <= 0:
        errors.append(f"{role.role}.timeout must be > 0")
    if not 0 <= role.temperature <= 2:
        errors.append(f"{role.role}.temperature must be between 0 and 2")
    if role.adapter in LOCAL_ADAPTERS:
        if role.adapter in {"whisper_cpp", "piper"}:
            if not role.binary_path or not Path(role.binary_path).exists():
                errors.append(f"{role.role}.binary_path does not exist for {role.adapter}")
            if not role.model_path or not Path(role.model_path).exists():
                errors.append(f"{role.role}.model_path does not exist for {role.adapter}")
        if role.adapter == "sherpa_onnx" and (not role.model_dir or not Path(role.model_dir).exists()):
            errors.append(f"{role.role}.model_dir does not exist for sherpa_onnx")
    return errors


def validate_profile_config(config: AppProfileConfig) -> list[str]:
    errors: list[str] = []
    for role in REQUIRED_ROLES:
        if role not in config.models:
            errors.append(f"missing required model role: {role}")
    for role in config.models.values():
        errors.extend(_validate_role(config, role))
    for provider in config.providers.values():
        if provider.name != "custom" and provider.api_key_env and provider.api_key_env.startswith("sk-"):
            errors.append(f"provider {provider.name} api_key_env must name an env var, not contain a key")
    return errors
