"""Environment helpers that keep secrets out of YAML files."""

from __future__ import annotations

import os


def env_status(name: str) -> dict[str, str | bool]:
    return {"env": name, "present": bool(os.environ.get(name))}


def read_env(name: str) -> str:
    return os.environ.get(name, "")


def mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 6:
        return "***"
    return f"{value[:2]}***{value[-2:]}"
