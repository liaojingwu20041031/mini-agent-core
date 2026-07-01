from pathlib import Path

from mini_agent.config.loader import load_profile_config
from mini_agent.config.validator import validate_profile_config


def _copy_config_with_models(tmp_path: Path, models_yaml: str) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    for name in ["providers", "agent", "voice", "tools", "mcp"]:
        (tmp_path / f"{name}.yaml").write_text(Path("config", f"{name}.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "models.yaml").write_text(models_yaml, encoding="utf-8")
    return tmp_path


def test_profile_config_loads_nested_yaml():
    config = load_profile_config("config", "local")

    assert config.role("main").provider == "local"
    assert config.role("main").model == ""
    assert config.providers["local"].example_models


def test_profile_check_fails_when_main_model_empty(tmp_path):
    _copy_config_with_models(
        tmp_path,
        "profiles:\n  local:\n    roles:\n      main:\n        provider: local\n        model: ''\n",
    )

    config = load_profile_config(tmp_path, "local")
    errors = validate_profile_config(config)

    assert any("main.model 必填" in error for error in errors)


def test_profile_check_local_success(tmp_path):
    config = load_profile_config(
        _copy_config_with_models(
            tmp_path,
            "profiles:\n  local:\n    roles:\n      main:\n        provider: local\n        model: test-model\n",
        ),
        "local",
    )

    assert validate_profile_config(config) == []


def test_provider_override_keeps_preset_base_url(tmp_path):
    config_dir = _copy_config_with_models(
        tmp_path,
        "profiles:\n  qwen:\n    roles:\n      main:\n        provider: qwen\n        model: test-model\n",
    )
    providers_path = config_dir / "providers.yaml"
    providers_path.write_text(
        "profiles:\n  qwen:\n    providers:\n      qwen:\n        api_key_env: QWEN_API_KEY\n",
        encoding="utf-8",
    )

    config = load_profile_config(config_dir, "qwen")

    assert config.providers["qwen"].base_url == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    assert config.providers["qwen"].api_key_env == "QWEN_API_KEY"


def test_qwen_check_explains_wrong_env_name(tmp_path, monkeypatch):
    monkeypatch.setenv("QWEN_API_KEY", "test-key")
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    config = load_profile_config(
        _copy_config_with_models(
            tmp_path,
            "profiles:\n  qwen:\n    roles:\n      main:\n        provider: qwen\n        model: qwen-plus\n",
        ),
        "qwen",
    )

    errors = validate_profile_config(config)

    assert any("DASHSCOPE_API_KEY" in error for error in errors)
    assert any("QWEN_API_KEY" in error and "默认不读取" in error for error in errors)


def test_domestic_ai_profiles_load_success(tmp_path, monkeypatch):
    env_by_profile = {
        "qwen": "DASHSCOPE_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "kimi": "MOONSHOT_API_KEY",
        "glm": "ZHIPUAI_API_KEY",
        "siliconflow": "SILICONFLOW_API_KEY",
    }
    for env_name in env_by_profile.values():
        monkeypatch.setenv(env_name, "test-key")

    models = "profiles:\n"
    for profile in env_by_profile:
        models += f"  {profile}:\n    roles:\n      main:\n        provider: {profile}\n        model: test-model\n"
    config_dir = _copy_config_with_models(tmp_path, models)

    for profile in env_by_profile:
        config = load_profile_config(config_dir, profile)

        assert config.role("main").provider == profile
        assert validate_profile_config(config) == []
