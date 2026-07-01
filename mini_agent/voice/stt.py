"""Speech-to-text interface."""

from __future__ import annotations

from typing import Protocol


class STT(Protocol):
    def transcribe(self, audio: bytes) -> str:
        """Convert audio bytes to text."""

