from mini_agent.config.schema import ModelRoleConfig, ProviderConfig
from mini_agent.models.registry import ModelRegistry, ProviderRegistry


def test_provider_registry_registers_aliases():
    registry = ProviderRegistry()
    provider = ProviderConfig(name="qwen", aliases=("dashscope",), base_url="https://example", api_key_env="KEY")

    registry.register(provider)

    assert registry.get("qwen") is provider
    assert registry.get("dashscope") is provider


def test_model_registry_returns_roles():
    registry = ModelRegistry()
    role = ModelRoleConfig(role="main", provider="local", model="explicit")

    registry.register(role)

    assert registry.get("main").model == "explicit"
