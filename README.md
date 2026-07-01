<p align="center">
  <img src="logo/logo.png" alt="mini-agent-core logo" width="160" />
</p>

<h1 align="center">mini-agent-core</h1>

<p align="center">
  <strong>轻量、可移植、国内 AI 友好的 Agent Core / SDK 模板</strong>
</p>

<p align="center">
  <code>OpenAI-compatible</code>
  · <code>CLI-first</code>
  · <code>ToolPack</code>
  · <code>AgentSpec</code>
  · <code>ROS2-ready</code>
</p>

<p align="center">
  初始化一次即可启动，不写死模型名，不默认启用危险工具，适合嵌入 CLI、APP、Web、机器人和 ARM 项目。
</p>

<p align="center">
  <a href="#快速开始">快速开始</a>
  · <a href="#为什么不写死模型名">模型配置</a>
  · <a href="#agent-自定义">Agent 自定义</a>
  · <a href="#工具与扩展">工具扩展</a>
  · <a href="#ros2--机器人接入">ROS2 接入</a>
</p>

---

## 一句话介绍

`mini-agent-core` 是一个可以嵌入 CLI、桌面 APP、Web 后台、机器人和 ARM 设备的轻量 Agent Core。它保留模型适配、Agent loop、工具系统、状态事件和 dummy 语音，不引入 LangChain、LangGraph、CrewAI、AutoGen，也不默认启用 MCP 或 danger 工具。

## 核心能力

| 能力         | 说明                                                                  |
| ------------ | --------------------------------------------------------------------- |
| 模型配置闭环 | `models list/use/check/doctor` 帮你查询、写入、验证模型 ID          |
| 一键启动     | `use` 一次后可直接 `start/chat/speak`                             |
| Agent 可配置 | `config/agents.yaml` 描述身份、能力、边界、风格                     |
| 工具可扩展   | `ToolDefinition` metadata、`tools describe`、ToolPack、Capability |
| 默认安全     | safe/confirm/danger 分级；danger 默认不注册                           |
| 可嵌入       | ROS2/APP/Web/ARM 项目可通过外部 ToolPack 注入能力                     |

## 快速开始

```powershell
cd mini-agent-core
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -e ".[dev]"
```

先选择 `<profile>`。远程服务 profile 需要先设置 API Key 环境变量；本地 profile 不需要 Key，但要先启动 OpenAI-compatible 服务。

```powershell
mini-agent init --profile <profile>

# 远程服务：按下方表格设置对应环境变量；本地服务可跳过这一行。
$env:<API_KEY_ENV>="你的 API Key"

# 本地服务：先启动 Ollama、LM Studio、llama.cpp server、vLLM 等 OpenAI-compatible 服务。
mini-agent models list --profile <profile>
mini-agent models use --profile <profile> --model "<从上一步复制的模型ID>"
mini-agent config check --profile <profile>
mini-agent use --profile <profile> --agent default
mini-agent start
```

常用 profile 与环境变量：

| profile         | 用途                        | API Key 环境变量        |
| --------------- | --------------------------- | ----------------------- |
| `local`       | 本地 OpenAI-compatible 服务 | 通常为空                |
| `qwen`        | 阿里云百炼 / DashScope      | `DASHSCOPE_API_KEY`   |
| `deepseek`    | DeepSeek                    | `DEEPSEEK_API_KEY`    |
| `kimi`        | Moonshot Kimi               | `MOONSHOT_API_KEY`    |
| `glm`         | 智谱 GLM                    | `ZHIPUAI_API_KEY`     |
| `siliconflow` | 硅基流动                    | `SILICONFLOW_API_KEY` |

如果你已经设置好 API Key 或本地服务，可以用向导模式：

```powershell
mini-agent init --profile <profile> --wizard
```

如果 provider 不支持 `/models`，就到服务商控制台或本地模型服务页面复制模型 ID，然后运行：

```powershell
mini-agent models use --profile <profile> --model "<模型ID>"
```

`<profile>` 可以是 `local`、`qwen`、`deepseek`、`kimi`、`glm`、`siliconflow`、`remote` 或你自己配置的 profile。README 不把任何厂商 profile 当默认选择。

## 为什么不写死模型名

模型 ID 会随服务商、地域、账号权限、本地部署和发布时间变化。项目不会在 CLI、state 或运行逻辑里替你猜模型名，也不会用 `provider.example_models` 当 fallback。`models list` 只显示服务端实时返回的 ID；`models use` 只写入你明确选择的 ID。

查看配置位置：

```powershell
mini-agent config where --profile <profile> --role main
```

默认 `config show` 不显示具体模型值：

```powershell
mini-agent config show --profile <profile>
mini-agent config show --profile <profile> --show-model
```

## 一次配置，后续启动

```powershell
mini-agent use --profile <profile> --agent default
mini-agent status
mini-agent start   # 等价文本交互
mini-agent chat    # 等价文本交互
mini-agent speak   # dummy 语音交互
```

`.mini-agent/state.json` 只保存 `default_profile`、`default_agent`、`default_mode`、`config_dir`，不保存模型名、base_url、API Key 或示例模型。

## Agent 自定义

复制 `config/agents.yaml.example` 为 `config/agents.yaml` 后，可以配置多个 Agent：

```yaml
agents:
  default:
    name: MiniAgent
    role: 通用轻量任务助手
    identity: 你是一个可嵌入项目的轻量 Agent Core。
    capabilities: [解释配置, 调用 safe 工具, 拆解任务]
    boundaries: [不保存密钥, 不绕过 danger 限制]
```

启动时选择：

```powershell
mini-agent text --profile <profile> --agent default
mini-agent use --profile <profile> --agent ros2_robot
```

## 工具与扩展

查看工具：

```powershell
mini-agent tools list --profile <profile>
mini-agent tools describe web_search --profile <profile>
```

`config/tools.yaml` 支持旧写法：

```yaml
enabled: [calculator, web_search]
```

也支持 ToolPack 写法：

```yaml
toolpacks:
  enabled: [builtin.basic, builtin.web]
tools:
  enabled: [calculator, fetch_url_text_public]
extensions:
  - module: project_tools.ros2_tools
    factory: build_ros2_toolpack
```

## ROS2 / 机器人接入

项目提供 `mini_agent.toolpacks.ros2_stub` 作为占位，不默认依赖 `rclpy`。真实 ROS2 工具建议放在你的机器人项目中，通过外部 ToolPack 注入。Agent 只做上层任务协调，不负责实时控制、急停、避障或底盘闭环。

## 文档

- [快速开始](docs/快速开始.md)
- [配置指南](docs/配置指南.md)
- [Agent与扩展](docs/Agent与扩展.md)
- [ROS2接入](docs/ROS2接入.md)
- [模型示例参考](docs/模型示例参考.md)
