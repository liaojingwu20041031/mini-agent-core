"""ROS2 integration placeholders without importing rclpy."""

from __future__ import annotations

from typing import Any

from mini_agent.core.tools import tool
from mini_agent.extensions.base import ToolPack


@tool(description="Get placeholder robot status for ROS2 integration.", category="ros2", namespace="ros2_stub")
def get_robot_status() -> dict[str, Any]:
    return {"ok": False, "note": "ROS2 stub: replace with project-specific robot status tool."}


@tool(description="Get placeholder navigation status for ROS2 integration.", category="ros2", namespace="ros2_stub")
def get_nav_status() -> dict[str, Any]:
    return {"ok": False, "note": "ROS2 stub: replace with project-specific navigation status tool."}


@tool(description="Placeholder map save command. Requires confirmation in real projects.", risk_level="confirm", category="ros2", namespace="ros2_stub")
def save_map(map_name: str) -> dict[str, Any]:
    return {"ok": False, "map_name": map_name, "note": "ROS2 stub: implement map saving in an external ToolPack."}


@tool(description="Placeholder patrol route command. Requires confirmation in real projects.", risk_level="confirm", category="ros2", namespace="ros2_stub")
def send_patrol_route(route: list[str]) -> dict[str, Any]:
    return {"ok": False, "route": route, "note": "ROS2 stub: implement patrol route dispatch in an external ToolPack."}


@tool(description="Danger placeholder for direct velocity command. Do not enable by default.", risk_level="danger", category="ros2", namespace="ros2_stub")
def send_velocity_command(linear_x: float, angular_z: float, duration_sec: float = 0.5) -> dict[str, Any]:
    return {
        "ok": False,
        "linear_x": linear_x,
        "angular_z": angular_z,
        "duration_sec": duration_sec,
        "note": "ROS2 stub: direct velocity control is danger-level and should stay disabled by default.",
    }


def build_ros2_stub_toolpack(include_danger: bool = False) -> ToolPack:
    tools = [get_robot_status, get_nav_status, save_map, send_patrol_route]
    if include_danger:
        tools.append(send_velocity_command)
    return ToolPack(name="ros2.stub", description="ROS2 placeholder tools without rclpy dependency.", tools=tools)
