"""Composable VoicePipeline: AudioInput -> STT -> AgentCore -> TTS -> AudioOutput."""

from __future__ import annotations

from dataclasses import dataclass

from mini_agent.core.agent import Agent
from mini_agent.voice.audio_input import AudioInput
from mini_agent.voice.audio_output import AudioOutput
from mini_agent.voice.stt import STT
from mini_agent.voice.tts import TTS
from mini_agent.voice.vad import VAD


@dataclass
class VoiceTurnResult:
    user_text: str
    agent_text: str
    audio: bytes


@dataclass(init=False)
class VoicePipeline:
    audio_input: AudioInput
    stt_engine: STT
    agent: Agent
    tts_engine: TTS
    audio_output: AudioOutput
    vad: VAD | None = None

    def __init__(
        self,
        audio_input: AudioInput,
        agent: Agent,
        audio_output: AudioOutput,
        stt_engine: STT | None = None,
        tts_engine: TTS | None = None,
        vad: VAD | None = None,
        stt: STT | None = None,
        tts: TTS | None = None,
    ) -> None:
        self.audio_input = audio_input
        self.stt_engine = stt_engine or stt
        self.agent = agent
        self.tts_engine = tts_engine or tts
        self.audio_output = audio_output
        self.vad = vad
        if self.stt_engine is None:
            raise ValueError("VoicePipeline requires stt_engine")
        if self.tts_engine is None:
            raise ValueError("VoicePipeline requires tts_engine")

    @property
    def stt(self) -> STT:
        return self.stt_engine

    @property
    def tts(self) -> TTS:
        return self.tts_engine

    def run_once(self) -> VoiceTurnResult:
        audio_in = self.audio_input.capture()
        if self.vad and not self.vad.is_speech(audio_in):
            return VoiceTurnResult(user_text="", agent_text="", audio=b"")
        user_text = self.stt_engine.transcribe(audio_in)
        agent_text = self.agent.run(user_text)
        audio_out = self.tts_engine.synthesize(agent_text)
        self.audio_output.play(audio_out)
        return VoiceTurnResult(user_text=user_text, agent_text=agent_text, audio=audio_out)
