"""Dummy STT adapter for tests and no-microphone demos."""

from __future__ import annotations


class DummySTT:
    def transcribe(self, audio: bytes) -> str:
        return audio.decode("utf-8") if audio else ""

