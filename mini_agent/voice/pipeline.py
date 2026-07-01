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


@dataclass
class VoicePipeline:
    audio_input: AudioInput
    stt: STT
    agent: Agent
    tts: TTS
    audio_output: AudioOutput
    vad: VAD | None = None

    def run_once(self) -> VoiceTurnResult:
        audio_in = self.audio_input.capture()
        if self.vad and not self.vad.is_speech(audio_in):
            return VoiceTurnResult(user_text="", agent_text="", audio=b"")
        user_text = self.stt.transcribe(audio_in)
        agent_text = self.agent.run(user_text)
        audio_out = self.tts.synthesize(agent_text)
        self.audio_output.play(audio_out)
        return VoiceTurnResult(user_text=user_text, agent_text=agent_text, audio=audio_out)

