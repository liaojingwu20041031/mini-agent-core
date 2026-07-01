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
| `web_search` | 无 Key 搜索公开网页，只返回来源和摘要 |
| `fetch_url_text` | 抓取公开 URL 正文，默认禁止内网 |
| `weather_open_meteo` | 查询 Open-Meteo 天气 |

## 默认联网工具

默认联网走 safe skill，不启动 MCP server。

| 技能 | 默认 profile | 边界 |
| --- | --- | --- |
| `web_search` | local/qwen/deepseek/kimi/glm/siliconflow/remote/online/edge | DuckDuckGo 免费页面解析，稳定性不如商业搜索 API |
| `weather_open_meteo` | local/qwen/deepseek/kimi/glm/siliconflow/remote/online | Open-Meteo 免费 API，适合原型和非商业场景 |
| `fetch_url_text` | online | 只抓公网 http/https，禁止 localhost、私有网段和 metadata IP |

联网工具只返回结构化结果，不替用户伪造事实结论。高可靠或商业场景请换成正式搜索 API 或付费天气 endpoint。

常见失败：

| 错误 | 含义 |
| --- | --- |
| `timeout` | 网络请求超时 |
| `empty_result` | 搜索页没有解析到结果 |
| `http_error` / `403` | 远端拒绝或不可达 |
| `city_not_found` | Open-Meteo 找不到城市 |
| `blocked_private_url` | URL 是内网、localhost 或解析到私有 IP |
| `parse_error` | 返回格式不符合预期 |

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
      - web_search
      - weather_open_meteo
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
