import pytest

from mini_agent.adapters.openai_compatible import OpenAICompatibleClient
from mini_agent.adapters.providers import list_provider_presets


def test_no_provider_exposes_default_model():
    assert all(not hasattr(preset, "default_model") for preset in list_provider_presets())


def test_from_provider_does_not_fill_model():
    with pytest.raises(ValueError, match="Model is required"):
        OpenAICompatibleClient.from_provider("deepseek", api_key="key")
