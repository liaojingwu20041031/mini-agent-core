"""Small config loader for .env, JSON, and simple YAML files."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mini_agent.adapters.providers import get_provider_preset


@dataclass
class AppConfig:
    llm_provider: str = "deepseek"
    llm_region: str = ""
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_timeout: float = 30
    llm_temperature: float = 0.2
    llm_extra_body_json: str = ""
    llm_enable_thinking: bool = False
    agent_max_steps: int = 5
    voice_stt_provider: str = "dummy"
    voice_tts_provider: str = "dummy"
    audio_input_device: str = ""
    audio_output_device: str = ""
    allow_danger_tools: bool = False


ENV_MAP = {
    "LLM_PROVIDER": "llm_provider",
    "LLM_REGION": "llm_region",
    "LLM_BASE_URL": "llm_base_url",
    "LLM_API_KEY": "llm_api_key",
    "LLM_MODEL": "llm_model",
    "LLM_TIMEOUT": "llm_timeout",
    "LLM_TEMPERATURE": "llm_temperature",
    "LLM_EXTRA_BODY_JSON": "llm_extra_body_json",
    "LLM_ENABLE_THINKING": "llm_enable_thinking",
    "AGENT_MAX_STEPS": "agent_max_steps",
    "VOICE_STT_PROVIDER": "voice_stt_provider",
    "VOICE_TTS_PROVIDER": "voice_tts_provider",
    "AUDIO_INPUT_DEVICE": "audio_input_device",
    "AUDIO_OUTPUT_DEVICE": "audio_output_device",
    "ALLOW_DANGER_TOOLS": "allow_danger_tools",
}


def _coerce(value: Any, current: Any) -> Any:
    if isinstance(current, bool):
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}
    if isinstance(current, int):
        return int(value)
    if isinstance(current, float):
        return float(value)
    return "" if value is None else str(value)


def load_dotenv(path: str | Path = ".env") -> dict[str, str]:
    env_path = Path(path)
    if not env_path.exists():
        return {}
    result: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def _load_simple_yaml(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if value.lower() in {"true", "false"}:
            parsed: Any = value.lower() == "true"
        else:
            parsed = value.strip('"').strip("'")
        data[key.strip()] = parsed
    return data


def parse_extra_body(config: AppConfig) -> dict[str, Any]:
    """Parse provider-specific extra JSON body from config."""

    extra: dict[str, Any] = {}
    if config.llm_extra_body_json:
        extra.update(json.loads(config.llm_extra_body_json))
    if config.llm_enable_thinking:
        extra.setdefault("thinking", {"type": "enabled"})
    return extra


def load_config(config_path: str | Path | None = None, env_path: str | Path = ".env") -> AppConfig:
    config = AppConfig()
    file_values: dict[str, Any] = {}
    if config_path:
        path = Path(config_path)
        if path.exists() and path.suffix.lower() == ".json":
            file_values = json.loads(path.read_text(encoding="utf-8"))
        elif path.exists() and path.suffix.lower() in {".yaml", ".yml"}:
            file_values = _load_simple_yaml(path)

    merged_env = load_dotenv(env_path)
    merged_env.update(os.environ)

    for env_key, attr in ENV_MAP.items():
        raw_value = file_values.get(env_key, file_values.get(attr))
        if env_key in merged_env:
            raw_value = merged_env[env_key]
        if raw_value is not None:
            setattr(config, attr, _coerce(raw_value, getattr(config, attr)))

    preset = get_provider_preset(config.llm_provider, config.llm_region)
    if not config.llm_base_url:
        config.llm_base_url = preset.base_url
    if not config.llm_model:
        raise ValueError("LLM model is required. Set LLM_MODEL or main.model in a profile config.")
    if not config.llm_api_key:
        config.llm_api_key = merged_env.get(preset.api_key_env, "")
    return config
