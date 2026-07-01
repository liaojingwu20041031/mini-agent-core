from mini_agent.adapters.stt_dummy import DummySTT
from mini_agent.adapters.tts_dummy import DummyTTS
from mini_agent.config.loader import load_profile_config
from mini_agent.models.factory import LLMFactory, STTFactory, TTSFactory, build_agent_from_profile


def test_stt_tts_factories_use_profile_roles():
    config = load_profile_config("config", "local")

    assert isinstance(STTFactory(config).create(), DummySTT)
    assert isinstance(TTSFactory(config).create(), DummyTTS)


def test_llm_factory_uses_explicit_model():
    config = load_profile_config("config", "local")
    llm = LLMFactory(config).create()

    assert llm.model == "qwen2.5:7b"
    assert llm.provider == "local"


def test_text_and_voice_can_share_agent_instance():
    config = load_profile_config("config", "local")
    agent = build_agent_from_profile(config)

    assert agent.llm.model == config.role("main").model
