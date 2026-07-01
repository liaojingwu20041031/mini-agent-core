"""Dummy TTS adapter for tests and no-speaker demos."""

from __future__ import annotations


class DummyTTS:
    def __init__(self) -> None:
        self.last_text = ""

    def synthesize(self, text: str) -> bytes:
        self.last_text = text
        return text.encode("utf-8")

