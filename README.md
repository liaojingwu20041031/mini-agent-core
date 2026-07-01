<p align="center">
  <img src="logo/logo.png" alt="mini-agent-core logo" width="160" />
</p>

<h1 align="center">mini-agent-core</h1>

<p align="center">
  <strong>一个轻量、可移植、国内 AI 友好的 Agent Core / SDK 模板</strong>
</p>

<p align="center">
  <code>OpenAI-compatible</code>
  · <code>CLI-first</code>
  · <code>ToolPack</code>
  · <code>AgentSpec</code>
  · <code>ROS2-ready</code>
</p>

<p align="center">
  面向真实项目集成：先用 CLI 跑通模型、Agent、工具和安全边界，再把同一套内核嵌入到 CLI、APP、Web、机器人或 ARM 项目。
</p>

<p align="center">
  <a href="#快速开始">快速开始</a>
  · <a href="#项目定位">项目定位</a>
  · <a href="#核心能力">核心能力</a>
  · <a href="#agent-自定义">Agent 自定义</a>
  · <a href="#工具与扩展">工具扩展</a>
  · <a href="#ros2--机器人接入">ROS2 接入</a>
</p>

---

## 项目定位

`mini-agent-core` 是一个可复用的轻量 Agent 内核。它保留模型适配、Agent loop、工具系统、状态事件和 dummy 语音管线，不绑定 LangChain、LangGraph、CrewAI、AutoGen，也不默认启用 MCP 或高风险工具。

它不是只为了演示效果的 demo，而是一个适合拿进项目继续生长的基础层：

- **CLI 可验证**：先在命令行里完成 provider、model、Agent、ToolPack 的闭环验证。
- **SDK 可嵌入**：核心能力集中在 `mini_agent` 包里，方便被桌面 APP、Web 后台、自动化任务或机器人系统调用。
- **配置可迁移**：provider、model、agent、tool、voice、MCP 都通过配置组织，减少业务代码里的硬编码。
- **安全有边界**：工具按 `safe` / `confirm` / `danger` 分级，危险能力不会默认注册。

## 适合场景

| 场景 | 适合怎么用 |
| --- | --- |
| 快速验证 Agent 方案 | 用 CLI 跑通模型配置、Agent loop、工具调用和状态事件 |
| 接入国内模型服务 | 通过 OpenAI-compatible 接口对接通义千问、DeepSeek、Kimi、GLM、硅基流动等服务 |
| 嵌入现有项目 | 把 `mini_agent` 作为轻量 SDK，引入 CLI、APP、Web 后台或自动化任务 |
| 扩展业务工具 | 使用 ToolPack、Capability 和 external extension 注入项目工具 |
| 机器人 / ARM 项目 | Agent 负责任务级协调，真实 ROS2 / 设备控制放在业务项目里实现 |

## 核心能力

| 能力 | 说明 |
| --- | --- |
| 模型配置闭环 | `models list/use/check/doctor` 覆盖查询、选择、写入和诊断 |
| 一次配置启动 | `use` 一次后可直接 `start`、`chat` 或 `speak` |
| Agent 可配置 | `config/agents.yaml` 描述身份、能力、边界和风格 |
| 工具可扩展 | 支持 `ToolDefinition` metadata、`tools describe`、ToolPack、Capability |
| 默认安全 | safe / confirm / danger 分级，danger 工具默认不注册 |
| 便于嵌入 | ROS2、APP、Web、ARM 项目可通过外部 ToolPack 注入能力 |

## 项目结构

```text
mini-agent-core/
├─ mini_agent/          # Agent Core、模型适配、CLI、工具系统、语音管线
├─ config/              # provider、model、agent、tool、voice、MCP 配置
├─ docs/                # 快速开始、配置指南、Agent 扩展、ROS2 接入
├─ examples/            # 文本、语音、工具、provider 示例
├─ edge/                # 面向边缘设备的 C++ tool runtime 占位示例
└─ tests/               # CLI、配置、工具、安全、模型、会话等测试
```

## 快速开始

```powershell
cd mini-agent-core
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -e ".[dev]"
```

选择一个 `<profile>`。远程服务需要先设置 API Key 环境变量；本地 profile 不需要 Key，但要先启动 Ollama、LM Studio、llama.cpp server、vLLM 等 OpenAI-compatible 服务。

```powershell
mini-agent init --profile <profile>

# 远程服务：按下方表格设置对应环境变量；本地服务可跳过。
$env:<API_KEY_ENV>="你的 API Key"

# 选择服务端真实存在的模型 ID。
mini-agent models list --profile <profile>
mini-agent models use --profile <profile> --model "<从上一步复制的模型ID>"

# 检查配置并启动。
mini-agent config check --profile <profile>
mini-agent use --profile <profile> --agent default
mini-agent start
```

常用 profile：

| profile | 用途 | API Key 环境变量 |
| --- | --- | --- |
| `local` | 本地 OpenAI-compatible 服务 | 通常为空 |
| `qwen` | 阿里云百炼 / DashScope | `DASHSCOPE_API_KEY` |
| `deepseek` | DeepSeek | `DEEPSEEK_API_KEY` |
| `kimi` | Moonshot Kimi | `MOONSHOT_API_KEY` |
| `glm` | 智谱 GLM | `ZHIPUAI_API_KEY` |
| `siliconflow` | 硅基流动 | `SILICONFLOW_API_KEY` |

也可以使用向导模式：

```powershell
mini-agent init --profile <profile> --wizard
```

如果 provider 不支持 `/models`，从服务商控制台或本地模型服务页面复制模型 ID，再手动写入：

```powershell
mini-agent models use --profile <profile> --model "<模型ID>"
```

`<profile>` 可以是 `local`、`qwen`、`deepseek`、`kimi`、`glm`、`siliconflow`、`remote`，也可以是你自己在配置中新增的 profile。

## 推荐使用路径

1. `mini-agent init --profile <profile>` 初始化配置。
2. `mini-agent models list --profile <profile>` 查看服务端实际可用模型。
3. `mini-agent models use --profile <profile> --model "<模型ID>"` 写入明确选择的模型。
4. `mini-agent config check --profile <profile>` 检查 profile、模型和环境变量。
5. `mini-agent use --profile <profile> --agent default` 固定默认 profile 与 Agent。
6. `mini-agent start` 或 `mini-agent chat` 进入文本交互。
7. 按项目需要扩展 Agent、ToolPack、MCP 或语音管线。

## 一次配置，后续启动

```powershell
mini-agent use --profile <profile> --agent default
mini-agent status
mini-agent start   # 文本交互
mini-agent chat    # 文本交互
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

建议把 Agent 的“能做什么”和“不能做什么”都写进配置。这样同一个 Agent 在 CLI、Web 后台、机器人项目中复用时，身份、能力和边界不会散落在业务代码里。

## 工具与扩展

查看当前工具：

```powershell
mini-agent tools list --profile <profile>
mini-agent tools describe web_search --profile <profile>
```

`config/tools.yaml` 支持直接启用工具：

```yaml
enabled: [calculator, web_search]
```

也支持 ToolPack 和外部 extension：

```yaml
toolpacks:
  enabled: [builtin.basic, builtin.web]
tools:
  enabled: [calculator, fetch_url_text_public]
extensions:
  - module: project_tools.ros2_tools
    factory: build_ros2_toolpack
```

推荐把通用能力放进内置或项目级 ToolPack，把业务能力放进外部 extension。这样 Agent Core 保持干净，业务项目可以独立迭代。

### 工具安全分级

| 分级 | 适合能力 | 默认策略 |
| --- | --- | --- |
| `safe` | 计算、只读查询、公开网页读取等低风险能力 | 可直接注册 |
| `confirm` | 需要用户确认的操作，例如发送请求、触发外部动作 | 注册前后保留确认链路 |
| `danger` | Shell、文件破坏性操作、生产环境写入等高风险能力 | 默认不注册 |

这套分级不是为了限制扩展，而是为了让 Agent 在进入真实业务系统前有清晰、可审计的安全边界。

## ROS2 / 机器人接入

项目提供 `mini_agent.toolpacks.ros2_stub` 作为占位，不默认依赖 `rclpy`。真实 ROS2 工具建议放在你的机器人项目中，通过外部 ToolPack 注入。

推荐接入方式：

1. 在机器人项目中实现 ROS2 ToolPack。
2. 在 `config/tools.yaml` 的 `extensions` 中注册 factory。
3. 让 Agent 只输出任务级意图。
4. 由 ROS2 节点负责实时控制、急停、避障和底盘闭环。

## 配置文件

| 文件 | 作用 |
| --- | --- |
| `config/providers.yaml` | provider、base_url、API Key 环境变量等配置 |
| `config/models.yaml` | 当前 profile 选择的模型 ID |
| `config/agents.yaml` | 多 Agent 身份、能力、边界和风格 |
| `config/tools.yaml` | ToolPack、工具启用列表和外部扩展 |
| `config/voice.yaml` | dummy / OpenAI / 本地语音相关配置 |
| `config/mcp.yaml` | MCP server 配置，默认不强制启用 |

真实 API Key 应放在环境变量中，不要写入仓库。

## 文档

- [快速开始](docs/快速开始.md)
- [配置指南](docs/配置指南.md)
- [Agent 与扩展](docs/Agent与扩展.md)
- [ROS2 接入](docs/ROS2接入.md)
- [模型示例参考](docs/模型示例参考.md)

## 开发与验证

```powershell
python -m pip install -e ".[dev]"
pytest
```

测试覆盖配置初始化、模型选择、OpenAI-compatible provider、工具安全、CLI 入口、会话状态和语音占位管线。对外展示或二次开发前，建议先跑完整测试。
