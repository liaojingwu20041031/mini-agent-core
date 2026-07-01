"""Factories that build runtime model adapters from profile roles."""

from __future__ import annotations

from mini_agent.adapters.openai_compatible import OpenAICompatibleClient
from mini_agent.adapters.stt_dummy import DummySTT
from mini_agent.adapters.stt_openai import OpenAISTT
from mini_agent.adapters.stt_sherpa_onnx import SherpaOnnxSTT
from mini_agent.adapters.stt_whisper_cpp import WhisperCppSTT
from mini_agent.adapters.tts_dummy import DummyTTS
from mini_agent.adapters.tts_openai import OpenAITTS
from mini_agent.adapters.tts_piper import PiperTTS
from mini_agent.config.env import read_env
from mini_agent.config.schema import AppProfileConfig, ModelRoleConfig, ProviderConfig
from mini_agent.core.agent import Agent
from mini_agent.core.guard import ToolGuard
from mini_agent.skills.registry import build_tool_registry


class LLMFactory:
    def __init__(self, config: AppProfileConfig) -> None:
        self.config = config

    def create(self, role: str = "main") -> OpenAICompatibleClient:
        model = self.config.role(role)
        provider = self._provider_for(model)
        if not model.model:
            raise ValueError(f"{role}.model is required")
        base_url = model.base_url or provider.base_url
        api_key_env = model.api_key_env or provider.api_key_env
        return OpenAICompatibleClient(
            base_url=base_url,
            api_key=read_env(api_key_env) if api_key_env else "",
            model=model.model,
            timeout=model.timeout,
            temperature=model.temperature,
            provider=provider.name,
            extra_body=model.extra_body,
        )

    def _provider_for(self, model: ModelRoleConfig) -> ProviderConfig:
        if model.provider not in self.config.providers:
            raise KeyError(f"Unknown provider for {model.role}: {model.provider}")
        return self.config.providers[model.provider]


class STTFactory:
    def __init__(self, config: AppProfileConfig) -> None:
        self.config = config

    def create(self, role: str = "stt"):
        cfg = self.config.models.get(role, ModelRoleConfig(role=role, adapter="dummy"))
        adapter = cfg.adapter or cfg.provider or "dummy"
        if adapter == "dummy":
            return DummySTT()
        if adapter == "openai":
            return OpenAISTT(api_key=read_env(cfg.api_key_env), model=cfg.model or "whisper-1")
        if adapter == "whisper_cpp":
            return WhisperCppSTT(binary_path=cfg.binary_path, model_path=cfg.model_path)
        if adapter == "sherpa_onnx":
            return SherpaOnnxSTT(model_dir=cfg.model_dir)
        raise ValueError(f"Unknown STT adapter: {adapter}")


class TTSFactory:
    def __init__(self, config: AppProfileConfig) -> None:
        self.config = config

    def create(self, role: str = "tts"):
        cfg = self.config.models.get(role, ModelRoleConfig(role=role, adapter="dummy"))
        adapter = cfg.adapter or cfg.provider or "dummy"
        if adapter == "dummy":
            return DummyTTS()
        if adapter == "openai":
            return OpenAITTS(api_key=read_env(cfg.api_key_env), model=cfg.model or "gpt-4o-mini-tts", voice=cfg.voice)
        if adapter == "piper":
            return PiperTTS(binary_path=cfg.binary_path, model_path=cfg.model_path)
        raise ValueError(f"Unknown TTS adapter: {adapter}")


def build_agent_from_profile(config: AppProfileConfig) -> Agent:
    llm = LLMFactory(config).create("main")
    tools = build_tool_registry(config.tools.enabled)
    return Agent(
        llm=llm,
        tools=tools,
        system_prompt=config.agent.system_prompt,
        max_steps=config.agent.max_steps,
        guard=ToolGuard(allow_danger=config.tools.allow_danger),
        session_max_messages=config.agent.max_messages,
        tool_result_max_chars=config.agent.tool_result_max_chars,
    )
