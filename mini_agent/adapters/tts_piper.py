"""Reserved Piper TTS adapter."""

from __future__ import annotations


class PiperTTS:
    def __init__(self, binary_path: str, model_path: str) -> None:
        self.binary_path = binary_path
        self.model_path = model_path

    def synthesize(self, text: str) -> bytes:
        raise NotImplementedError("TODO V0.2: call Piper with configured binary/model paths.")

