"""Optional OpenAI-compatible cloud STT adapter placeholder."""

from __future__ import annotations


class OpenAISTT:
    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise ValueError("OpenAISTT requires an API key.")
        self.api_key = api_key
        self.model = model

    def transcribe(self, audio: bytes) -> str:
        raise NotImplementedError("Cloud STT upload is intentionally left optional for V0.1.")
