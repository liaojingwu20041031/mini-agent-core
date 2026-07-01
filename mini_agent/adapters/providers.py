"""Provider presets for domestic OpenAI-compatible model services."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderPreset:
    """Public connection metadata for one OpenAI-compatible provider."""

    name: str
    aliases: tuple[str, ...]
    base_url: str
    api_key_env: str
    note: str = ""
    example_models: tuple[str, ...] = ()


_PROVIDERS: dict[str, ProviderPreset] = {}


def _register(preset: ProviderPreset) -> None:
    _PROVIDERS[preset.name] = preset
    for alias in preset.aliases:
        _PROVIDERS[alias] = preset


_register(
    ProviderPreset(
        name="deepseek",
        aliases=("ds",),
        base_url="https://api.deepseek.com",
        api_key_env="DEEPSEEK_API_KEY",
        note="DeepSeek OpenAI-compatible API. Use deepseek-v4-pro for stronger reasoning.",
        example_models=("deepseek-v4-flash", "deepseek-v4-pro"),
    )
)
_register(
    ProviderPreset(
        name="qwen",
        aliases=("dashscope", "aliyun", "bailian", "tongyi"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key_env="DASHSCOPE_API_KEY",
        note="Alibaba Cloud Bailian/DashScope OpenAI-compatible endpoint.",
        example_models=("qwen-plus", "qwen-max"),
    )
)
_register(
    ProviderPreset(
        name="kimi",
        aliases=("moonshot",),
        base_url="https://api.moonshot.cn/v1",
        api_key_env="MOONSHOT_API_KEY",
        note="Moonshot Kimi OpenAI-compatible API.",
        example_models=("kimi-k2.6",),
    )
)
_register(
    ProviderPreset(
        name="glm",
        aliases=("zhipu", "bigmodel", "zai"),
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key_env="ZHIPUAI_API_KEY",
        note="Zhipu/BigModel OpenAI-compatible API preset.",
        example_models=("glm-4.5",),
    )
)
_register(
    ProviderPreset(
        name="siliconflow",
        aliases=("sf", "guiji", "silicon"),
        base_url="https://api.siliconflow.cn/v1",
        api_key_env="SILICONFLOW_API_KEY",
        note="SiliconFlow OpenAI-compatible API preset.",
        example_models=("deepseek-ai/DeepSeek-V3.1",),
    )
)
_register(
    ProviderPreset(
        name="openai",
        aliases=("foreign", "global"),
        base_url="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
        note="Generic OpenAI preset kept for compatibility.",
        example_models=("gpt-4o-mini",),
    )
)
_register(
    ProviderPreset(
        name="custom",
        aliases=("compatible",),
        base_url="",
        api_key_env="CUSTOM_LLM_API_KEY",
        note="User-provided OpenAI-compatible endpoint. Configure base_url and model in profile YAML.",
        example_models=(),
    )
)
_register(
    ProviderPreset(
        name="local",
        aliases=("ollama", "lmstudio", "llama_cpp", "vllm"),
        base_url="http://localhost:11434/v1",
        api_key_env="LOCAL_LLM_API_KEY",
        note="Local OpenAI-compatible server preset.",
        example_models=("qwen2.5:7b", "llama3.1:8b"),
    )
)


def get_provider_preset(name: str | None, region: str | None = None) -> ProviderPreset:
    """Return a provider preset by name or alias."""

    key = (name or "deepseek").strip().lower()
    preset = _PROVIDERS.get(key)
    if not preset:
        supported = ", ".join(sorted({item.name for item in _PROVIDERS.values()}))
        raise ValueError(f"Unknown LLM provider: {name!r}. Supported providers: {supported}")

    if preset.name == "qwen" and region:
        region_key = region.strip().lower()
        if region_key in {"us", "virginia"}:
            return ProviderPreset(
                name=preset.name,
                aliases=preset.aliases,
                base_url="https://dashscope-us.aliyuncs.com/compatible-mode/v1",
                api_key_env=preset.api_key_env,
                note=preset.note,
                example_models=preset.example_models,
            )
    return preset


def list_provider_presets() -> list[ProviderPreset]:
    """Return unique provider presets."""

    unique: dict[str, ProviderPreset] = {}
    for preset in _PROVIDERS.values():
        unique[preset.name] = preset
    return list(unique.values())
