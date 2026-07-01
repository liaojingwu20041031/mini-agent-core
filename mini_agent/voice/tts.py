"""Text-to-speech interface."""

from __future__ import annotations

from typing import Protocol


class TTS(Protocol):
    def synthesize(self, text: str) -> bytes:
        """Convert text to audio bytes."""

