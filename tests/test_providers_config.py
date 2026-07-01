import json

import pytest

from mini_agent.adapters.providers import get_provider_preset
from mini_agent.core.config import load_config, parse_extra_body


def test_provider_aliases_resolve_to_expected_presets():
    assert get_provider_preset("deepseek").name == "deepseek"
    assert get_provider_preset("qwen").name == "qwen"
    assert get_provider_preset("dashscope").name == "qwen"
    assert get_provider_preset("kimi").name == "kimi"
    assert get_provider_preset("moonshot").name == "kimi"


def test_provider_presets_have_examples_not_defaults():
    deepseek = get_provider_preset("deepseek")
    qwen = get_provider_preset("qwen")
    kimi = get_provider_preset("kimi")

    assert deepseek.base_url == "https://api.deepseek.com"
    assert not hasattr(deepseek, "default_model")
    assert "deepseek-v4-flash" in deepseek.example_models
    assert qwen.base_url == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    assert "qwen-plus" in qwen.example_models
    assert kimi.base_url == "https://api.moonshot.cn/v1"
    assert "kimi-k2.6" in kimi.example_models


def test_config_custom_base_url_overrides_provider(tmp_path, monkeypatch):
    for key in ["LLM_PROVIDER", "LLM_BASE_URL", "LLM_MODEL", "LLM_API_KEY", "DEEPSEEK_API_KEY"]:
        monkeypatch.delenv(key, raising=False)
    env_path = tmp_path / ".env"
    env_path.write_text(
        "LLM_PROVIDER=deepseek\n"
        "LLM_BASE_URL=http://localhost:8000/v1\n"
        "LLM_MODEL=my-local-model\n"
        "LLM_API_KEY=test-key\n",
        encoding="utf-8",
    )

    config = load_config(env_path=env_path)

    assert config.llm_provider == "deepseek"
    assert config.llm_base_url == "http://localhost:8000/v1"
    assert config.llm_model == "my-local-model"
    assert config.llm_api_key == "test-key"


def test_config_uses_provider_key_but_requires_model(tmp_path, monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "dashscope-key")
    env_path = tmp_path / ".env"
    env_path.write_text("LLM_PROVIDER=qwen\n", encoding="utf-8")

    with pytest.raises(ValueError, match="LLM model is required"):
        load_config(env_path=env_path)


def test_parse_extra_body_merges_json_and_thinking(monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "explicit-model")
    config = load_config(env_path="missing.env")
    config.llm_extra_body_json = json.dumps({"top_p": 0.8})
    config.llm_enable_thinking = True

    extra = parse_extra_body(config)

    assert extra["top_p"] == 0.8
    assert extra["thinking"] == {"type": "enabled"}
