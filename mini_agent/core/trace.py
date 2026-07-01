"""Small logging helpers for LLM and tool traces."""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator


LOGGER_NAME = "mini_agent"
_DEBUG_ENABLED = False


def configure_logging(debug: bool = False) -> None:
    global _DEBUG_ENABLED
    _DEBUG_ENABLED = debug
    logger = get_logger()
    logger.setLevel(logging.INFO if debug else logging.WARNING)


def get_logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO if _DEBUG_ENABLED else logging.WARNING)
    return logger


@dataclass
class TraceEvent:
    name: str
    elapsed_ms: float
    ok: bool = True
    detail: str | None = None


@contextmanager
def trace_span(name: str, detail: str | None = None) -> Iterator[None]:
    logger = get_logger()
    started = time.perf_counter()
    try:
        yield
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.exception("%s failed in %.1fms: %s", name, elapsed_ms, exc)
        raise
    else:
        elapsed_ms = (time.perf_counter() - started) * 1000
        if detail:
            logger.info("%s finished in %.1fms: %s", name, elapsed_ms, detail)
        else:
            logger.info("%s finished in %.1fms", name, elapsed_ms)
