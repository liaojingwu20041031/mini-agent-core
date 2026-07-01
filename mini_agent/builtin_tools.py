"""Compatibility exports for built-in tools.

New code should use mini_agent.skills.registry. This module registers only
default safe tools, so dangerous_shell is no longer enabled by default.
"""

from __future__ import annotations

from mini_agent.skills.builtin.confirm import set_mock_led
from mini_agent.skills.builtin.danger import dangerous_shell, shell_exec
from mini_agent.skills.builtin.safe import calculator as calculate
from mini_agent.skills.builtin.safe import get_time_local as get_time
from mini_agent.skills.builtin.safe import system_status as get_system_status
from mini_agent.skills.registry import DEFAULT_SAFE_SKILLS, SAFE_SKILLS


def read_mock_sensor(sensor_name: str) -> dict[str, float | str]:
    values = {"temperature": 24.5, "humidity": 52.0, "distance": 1.25}
    return {"sensor": sensor_name, "value": values.get(sensor_name, 0.0)}


def register_builtin_tools(registry) -> None:
    registry.register_many([SAFE_SKILLS[name] for name in DEFAULT_SAFE_SKILLS])
