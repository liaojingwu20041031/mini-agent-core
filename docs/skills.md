# 技能库说明

`mini-agent-core` 把内置技能分成 `safe`、`confirm`、`danger` 三类。默认只建议启用 safe 技能。

## 默认 safe 技能

| 技能 | 用途 |
| --- | --- |
| `calculator` | 计算简单表达式 |
| `unit_convert` | 常见单位换算 |
| `format_json` | 格式化 JSON 文本 |
| `summarize_text` | 摘要文本 |
| `extract_key_points` | 提取要点 |
| `translate_text` | 简单翻译 |
| `plan_task` | 拆解任务 |
| `get_time_local` | 获取本地时间 |
| `system_status` | 查看轻量系统状态 |
| `config_get` | 查询配置项 |
| `tool_list` | 列出工具 |

## confirm 技能

confirm 技能会改变外部状态，例如写入记忆、写文件、控制设备。它们需要确认回调同意后才执行。

常见技能：

| 技能 | 用途 |
| --- | --- |
| `memory_write` | 写入一段简单记忆 |
| `set_mock_led` | 控制模拟 LED |
| `file_write_sandbox` | 在 sandbox 内写文件 |

## danger 技能

danger 技能风险最高，例如执行 shell。默认不注册，也不建议新手启用。

| 技能 | 风险 |
| --- | --- |
| `dangerous_shell` | 可执行系统命令 |
| `shell_exec` | 可执行系统命令 |

## 在 tools.yaml 启用技能

```yaml
profiles:
  local:
    enabled:
      - calculator
      - get_time_local
      - tool_list
    allow_danger: false
```

如果启用 danger 技能，必须同时显式设置：

```yaml
allow_danger: true
```

## 注册自己的工具

```python
from mini_agent.core.tools import ToolRegistry, tool

@tool(description="读取传感器", risk_level="safe")
def read_sensor(name: str) -> dict:
    return {"name": name, "value": 42}

registry = ToolRegistry()
registry.register(read_sensor)
```

## 设置 risk_level

```python
@tool(description="写入文件", risk_level="confirm")
def write_file(path: str, content: str) -> dict:
    return {"path": path, "written": len(content)}
```

可选值：

- `safe`：只读或低风险。
- `confirm`：需要用户确认。
- `danger`：高风险，默认禁用。
