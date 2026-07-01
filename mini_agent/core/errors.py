"""Shared exception types for Mini Agent Core."""

from __future__ import annotations


class AgentError(RuntimeError):
    """Raised when an agent operation fails with a user-readable message."""
