"""Interaction interface."""

from __future__ import annotations

from typing import Protocol


class Interaction(Protocol):
    def run(self) -> None:
        """Start the interaction loop."""

