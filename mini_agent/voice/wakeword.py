"""Wake word interface reserved for later always-listening modes."""

from __future__ import annotations

from typing import Protocol


class WakeWordDetector(Protocol):
    def detected(self, audio: bytes) -> bool:
        """Return True when a wake word is detected."""

