from pathlib import Path

from mini_agent.config.loader import load_profile_config
from mini_agent.config.validator import validate_profile_config


def test_profile_config_loads_nested_yaml():
    config = load_profile_config("config", "local")

    assert config.role("main").provider == "local"
    assert config.role("main").model == "qwen2.5:7b"
    assert config.providers["local"].example_models


def test_profile_check_fails_when_main_model_empty(tmp_path):
    for name in ["providers", "agent", "voice", "tools", "mcp"]:
        (tmp_path / f"{name}.yaml").write_text(Path("config", f"{name}.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "models.yaml").write_text(
        "profiles:\n  local:\n    roles:\n      main:\n        provider: local\n        model: ''\n",
        encoding="utf-8",
    )

    config = load_profile_config(tmp_path, "local")
    errors = validate_profile_config(config)

    assert any("main.model is required" in error for error in errors)


def test_profile_check_local_success():
    config = load_profile_config("config", "local")

    assert validate_profile_config(config) == []


def test_domestic_ai_profiles_load_success(monkeypatch):
    env_by_profile = {
        "qwen": "DASHSCOPE_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "kimi": "MOONSHOT_API_KEY",
        "glm": "ZHIPUAI_API_KEY",
        "siliconflow": "SILICONFLOW_API_KEY",
    }
    for env_name in env_by_profile.values():
        monkeypatch.setenv(env_name, "test-key")

    for profile in env_by_profile:
        config = load_profile_config("config", profile)

        assert config.role("main").provider == profile
        assert validate_profile_config(config) == []
