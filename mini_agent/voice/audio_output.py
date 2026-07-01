"""Audio output interfaces and dummy text output."""

from __future__ import annotations

from typing import Protocol


class AudioOutput(Protocol):
    def play(self, audio: bytes) -> None:
        """Play one synthesized response."""


class TextAudioOutput:
    def __init__(self) -> None:
        self.last_audio = b""

    def play(self, audio: bytes) -> None:
        self.last_audio = audio
        print(audio.decode("utf-8", errors="replace"))

