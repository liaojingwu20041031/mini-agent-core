from mini_agent.adapters.stt_dummy import DummySTT
from mini_agent.adapters.tts_dummy import DummyTTS
from mini_agent.config.schema import AgentRuntimeConfig, AppProfileConfig, ModelRoleConfig, ProviderConfig, ToolsConfig
from mini_agent.models.factory import LLMFactory, STTFactory, TTSFactory, build_agent_from_profile


def _profile_config() -> AppProfileConfig:
    return AppProfileConfig(
        profile="test",
        providers={"local": ProviderConfig(name="local", base_url="http://localhost:11434/v1", api_key_env="")},
        models={
            "main": ModelRoleConfig(role="main", provider="local", model="explicit-model"),
            "stt": ModelRoleConfig(role="stt", adapter="dummy"),
            "tts": ModelRoleConfig(role="tts", adapter="dummy"),
        },
        agent=AgentRuntimeConfig(max_steps=5),
        tools=ToolsConfig(enabled=("calculator",), allow_danger=False),
    )


def test_stt_tts_factories_use_profile_roles():
    config = _profile_config()

    assert isinstance(STTFactory(config).create(), DummySTT)
    assert isinstance(TTSFactory(config).create(), DummyTTS)


def test_llm_factory_uses_explicit_model():
    config = _profile_config()
    llm = LLMFactory(config).create()

    assert llm.model == "explicit-model"
    assert llm.provider == "local"


def test_text_and_voice_can_share_agent_instance():
    config = _profile_config()
    agent = build_agent_from_profile(config)

    assert agent.llm.model == config.role("main").model
