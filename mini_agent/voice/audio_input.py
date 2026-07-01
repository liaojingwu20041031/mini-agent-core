"""Audio input interfaces and dummy push-to-talk input."""

from __future__ import annotations

from typing import Callable, Protocol


class AudioInput(Protocol):
    def capture(self) -> bytes:
        """Capture one utterance."""


class TextAudioInput:
    """Turns typed text into bytes so VoicePipeline can be tested without audio hardware."""

    def __init__(self, text_provider: Callable[[], str] | None = None) -> None:
        self.text_provider = text_provider or input

    def capture(self) -> bytes:
        return self.text_provider().encode("utf-8")

