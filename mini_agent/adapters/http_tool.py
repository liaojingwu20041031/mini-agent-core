"""Small helper for future HTTP-backed tools."""

from __future__ import annotations

from typing import Any


def post_json(url: str, payload: dict[str, Any], timeout: float = 10) -> dict[str, Any]:
    try:
        import httpx
    except ImportError as exc:
        raise RuntimeError("Install httpx to use HTTP tool helpers.") from exc
    response = httpx.post(url, json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()

