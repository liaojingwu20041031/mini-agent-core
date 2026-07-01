import pytest

from mini_agent.adapters.openai_compatible import OpenAICompatibleClient
from mini_agent.adapters.providers import list_provider_presets
from mini_agent.core.config import load_config


def test_no_provider_exposes_default_model():
    assert all(not hasattr(preset, "default_model") for preset in list_provider_presets())


def test_load_config_does_not_fill_model_from_provider(tmp_path, monkeypatch):
    monkeypatch.delenv("LLM_MODEL", raising=False)
    env_path = tmp_path / ".env"
    env_path.write_text("LLM_PROVIDER=deepseek\n", encoding="utf-8")

    with pytest.raises(ValueError, match="LLM model is required"):
        load_config(env_path=env_path)


def test_from_provider_does_not_fill_model():
    with pytest.raises(ValueError, match="Model is required"):
        OpenAICompatibleClient.from_provider("deepseek", api_key="key")
