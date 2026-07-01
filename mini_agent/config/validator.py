"""Validation for profile configuration."""

from __future__ import annotations

from pathlib import Path

from mini_agent.config.env import env_status
from mini_agent.config.schema import AppProfileConfig, ModelRoleConfig

REQUIRED_ROLES = ("main",)
VALID_ROLES = {"main", "stt", "tts", "embedding", "small"}
LOCAL_ADAPTERS = {"whisper_cpp", "sherpa_onnx", "piper"}
PROFILE_ENV_HINTS = {
    "qwen": ("DASHSCOPE_API_KEY", ("QWEN_API_KEY", "DEEPSEEK_API_KEY")),
    "deepseek": ("DEEPSEEK_API_KEY", ("DASHSCOPE_API_KEY", "QWEN_API_KEY")),
    "kimi": ("MOONSHOT_API_KEY", ()),
    "glm": ("ZHIPUAI_API_KEY", ()),
    "siliconflow": ("SILICONFLOW_API_KEY", ()),
    "remote": ("OPENAI_API_KEY", ()),
}


def _env_missing_message(config: AppProfileConfig, provider_name: str, api_key_env: str) -> list[str]:
    errors = [
        f"当前 profile '{config.profile}' 的 main.provider 是 '{provider_name}'，需要设置环境变量 {api_key_env}。",
        f"请在 PowerShell 运行：$env:{api_key_env}=\"你的 API Key\"，不要把真实 Key 写进 YAML。",
    ]
    expected, common_wrong = PROFILE_ENV_HINTS.get(config.profile, (api_key_env, ()))
    detected_wrong = [name for name in common_wrong if env_status(name)["present"]]
    if detected_wrong:
        if "QWEN_API_KEY" in detected_wrong:
            errors.append(
                "检测到你设置了 QWEN_API_KEY，但 qwen profile 默认不读取它；"
                "如果你想用这个变量名，请在 config/providers.yaml 中覆盖 qwen.api_key_env。"
            )
        if "DEEPSEEK_API_KEY" in detected_wrong:
            errors.append(
                "检测到你设置了 DEEPSEEK_API_KEY，但它属于 deepseek profile；"
                "如果你使用的是 DeepSeek Key，请运行 mini-agent config check --profile deepseek。"
            )
        other_wrong = [name for name in detected_wrong if name not in {"QWEN_API_KEY", "DEEPSEEK_API_KEY"}]
        if other_wrong:
            joined = ", ".join(other_wrong)
            errors.append(f"检测到你设置了 {joined}，但 profile '{config.profile}' 默认不读取这些变量。")
    if expected != api_key_env:
        errors.append(f"提示：profile '{config.profile}' 的常用环境变量是 {expected}，当前配置要求 {api_key_env}。")
    return errors


def _validate_role(config: AppProfileConfig, role: ModelRoleConfig) -> list[str]:
    errors: list[str] = []
    if role.role not in VALID_ROLES:
        errors.append(f"未知模型角色 {role.role!r}；可选角色：{sorted(VALID_ROLES)}")
    if role.role == "main" and not role.model.strip():
        errors.append("main.model 必填；请在 config/models.yaml 的当前 profile 下填写 roles.main.model。")
    provider_name = role.provider
    if provider_name and provider_name not in config.providers and role.role == "main":
        errors.append(f"main.provider {provider_name!r} 未配置；请检查 config/providers.yaml 或内置 provider 名。")
    provider = config.providers.get(provider_name)
    base_url = role.base_url or (provider.base_url if provider else "")
    if role.role == "main" and not base_url:
        errors.append("main.base_url 必填；请在当前 role 或 provider 配置中填写 OpenAI-compatible base_url。")
    api_key_env = role.api_key_env or (provider.api_key_env if provider else "")
    if role.role == "main" and api_key_env and not env_status(api_key_env)["present"]:
        errors.extend(_env_missing_message(config, provider_name, api_key_env))
    if role.timeout <= 0:
        errors.append(f"{role.role}.timeout 必须大于 0")
    if not 0 <= role.temperature <= 2:
        errors.append(f"{role.role}.temperature 必须在 0 到 2 之间")
    if role.adapter in LOCAL_ADAPTERS:
        if role.adapter in {"whisper_cpp", "piper"}:
            if not role.binary_path or not Path(role.binary_path).exists():
                errors.append(f"{role.role}.binary_path 不存在，adapter={role.adapter}")
            if not role.model_path or not Path(role.model_path).exists():
                errors.append(f"{role.role}.model_path 不存在，adapter={role.adapter}")
        if role.adapter == "sherpa_onnx" and (not role.model_dir or not Path(role.model_dir).exists()):
            errors.append(f"{role.role}.model_dir 不存在，adapter=sherpa_onnx")
    return errors


def validate_profile_config(config: AppProfileConfig) -> list[str]:
    errors: list[str] = []
    for role in REQUIRED_ROLES:
        if role not in config.models:
            errors.append(f"缺少必需模型角色：{role}")
    for role in config.models.values():
        errors.extend(_validate_role(config, role))
    for provider in config.providers.values():
        if provider.name != "custom" and provider.api_key_env and provider.api_key_env.startswith("sk-"):
            errors.append(f"provider {provider.name} 的 api_key_env 必须是环境变量名，不能写真实 API Key")
    return errors
