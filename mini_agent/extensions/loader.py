"""Load external ToolPack factories without requiring entry points."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from mini_agent.extensions.base import ToolPack


def load_external_toolpack(spec: dict[str, Any]) -> ToolPack:
    module_name = str(spec.get("module", "")).strip()
    factory_name = str(spec.get("factory", "")).strip()
    if not module_name or not factory_name:
        raise ValueError("extensions 项必须包含 module 和 factory")
    try:
        module = import_module(module_name)
        factory = getattr(module, factory_name)
        pack = factory()
    except Exception as exc:
        raise RuntimeError(f"加载外部 ToolPack 失败：{module_name}.{factory_name}: {type(exc).__name__}: {exc}") from exc
    if not isinstance(pack, ToolPack):
        raise TypeError(f"{module_name}.{factory_name} 必须返回 ToolPack")
    return pack
