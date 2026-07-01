from mini_agent.adapters.providers import get_provider_preset


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
