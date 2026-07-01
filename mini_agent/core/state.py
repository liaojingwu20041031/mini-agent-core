"""Local CLI state with an explicit safe allow-list."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


STATE_DIR = ".mini-agent"
STATE_FILE = "state.json"
SAFE_STATE_KEYS = {"default_profile", "default_agent", "default_mode", "config_dir"}


@dataclass
class MiniAgentState:
    default_profile: str = ""
    default_agent: str = "default"
    default_mode: str = "text"
    config_dir: str = "config"


def state_path(root: str | Path = ".") -> Path:
    return Path(root) / STATE_DIR / STATE_FILE


def load_state(root: str | Path = ".") -> MiniAgentState | None:
    path = state_path(root)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"状态文件格式错误：{path}")
    safe_data: dict[str, Any] = {key: data.get(key, "") for key in SAFE_STATE_KEYS}
    return MiniAgentState(
        default_profile=str(safe_data.get("default_profile") or ""),
        default_agent=str(safe_data.get("default_agent") or "default"),
        default_mode=str(safe_data.get("default_mode") or "text"),
        config_dir=str(safe_data.get("config_dir") or "config"),
    )


def save_state(state: MiniAgentState, root: str | Path = ".") -> Path:
    path = state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {key: value for key, value in asdict(state).items() if key in SAFE_STATE_KEYS}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
