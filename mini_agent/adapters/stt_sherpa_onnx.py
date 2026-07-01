"""Reserved sherpa-onnx STT adapter."""

from __future__ import annotations


class SherpaOnnxSTT:
    def __init__(self, model_dir: str) -> None:
        self.model_dir = model_dir

    def transcribe(self, audio: bytes) -> str:
        raise NotImplementedError("TODO V0.2: integrate sherpa-onnx runtime.")

