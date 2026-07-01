"""Reserved whisper.cpp STT adapter."""

from __future__ import annotations


class WhisperCppSTT:
    def __init__(self, binary_path: str, model_path: str) -> None:
        self.binary_path = binary_path
        self.model_path = model_path

    def transcribe(self, audio: bytes) -> str:
        raise NotImplementedError("TODO V0.2: call whisper.cpp with configured binary/model paths.")

