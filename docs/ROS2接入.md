# ROS2 接入

`mini-agent-core` 提供 `mini_agent.toolpacks.ros2_stub` 作为 ROS2 接入占位，但默认不依赖 `rclpy`。

## 定位

Agent 是上层任务协调者，适合：

- 理解用户意图。
- 查询机器人和导航状态。
- 拆解巡检任务。
- 在确认后调用高层 service/action。

Agent 不是实时控制器，不负责底盘闭环、急停、避障、安全联锁或硬实时运动控制。

## 风险分级建议

| 操作 | 风险等级 |
| --- | --- |
| 查询机器人状态 | safe |
| 查询导航状态 | safe |
| 保存地图 | confirm |
| 下发巡检路线 | confirm |
| 直接速度控制 | danger，默认不启用 |

## 真实项目接入

在 ROS2 项目中实现自己的 ToolPack：

```python
from mini_agent.extensions.base import ToolPack
from mini_agent.core.tools import tool

@tool(description="Get robot status.")
def get_robot_status() -> dict:
    return {"battery": 0.8, "mode": "idle"}

def build_ros2_toolpack() -> ToolPack:
    return ToolPack(
        name="project.ros2",
        description="项目 ROS2 工具",
        tools=[get_robot_status],
    )
```

`config/tools.yaml`：

```yaml
extensions:
  - module: project_tools.ros2_tools
    factory: build_ros2_toolpack
```

不要把 `rclpy` 加入 `mini-agent-core` 默认依赖。真实 ROS2 依赖应留在机器人项目自己的环境里。
