"""Voice activity detection boundary."""

from __future__ import annotations

from typing import Protocol


class VAD(Protocol):
    def is_speech(self, frame: bytes) -> bool:
        """Return whether a frame contains speech."""


class NoOpVAD:
    def is_speech(self, frame: bytes) -> bool:
        return bool(frame)

