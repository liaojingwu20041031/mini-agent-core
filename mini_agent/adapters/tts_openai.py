"""Optional OpenAI-compatible cloud TTS adapter placeholder."""

from __future__ import annotations


class OpenAITTS:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini-tts", voice: str = "alloy") -> None:
        if not api_key:
            raise ValueError("OpenAITTS requires an API key.")
        self.api_key = api_key
        self.model = model
        self.voice = voice

    def synthesize(self, text: str) -> bytes:
        raise NotImplementedError("Cloud TTS is intentionally left optional for V0.1.")

