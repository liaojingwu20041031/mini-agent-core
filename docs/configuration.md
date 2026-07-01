# 配置指南

`mini-agent-core` 统一使用 YAML profile。旧 `.env` / `LLM_*` 配置入口已经移除；项目只读取系统环境变量本身，不解析 `.env` 文件。

## 配置文件

运行时默认读取 `config/` 下的 6 个 YAML 文件：

| 文件 | 说明 |
| --- | --- |
| `providers.yaml` | provider 连接信息，通常不用改 |
| `models.yaml` | 主模型、STT、TTS、小模型、向量模型 |
| `agent.yaml` | Agent 步数、上下文长度、系统提示词 |
| `voice.yaml` | 音频输入输出设备 |
| `tools.yaml` | 内置技能启用列表 |
| `mcp.yaml` | MCP server profile，默认关闭 |

`quickstart.yaml.example` 是给新手看的“一文件配置参考”，当前运行时不读取它。

## Profile

每个 YAML 都支持 `profiles`。同一个 profile 会跨 6 个文件合并成一个运行配置。

常用 profile：

| Profile | 用途 |
| --- | --- |
| `local` | 本地 OpenAI-compatible 服务 |
| `qwen` | 阿里云百炼 / DashScope |
| `deepseek` | DeepSeek |
| `kimi` | Moonshot Kimi |
| `glm` | 智谱 GLM |
| `siliconflow` | 硅基流动 |
| `remote` | OpenAI 或其他远程通用服务 |
| `online` | 默认启用更多联网 safe 工具 |
| `minimal` | 最小工具集，不默认联网 |
| `edge` | ARM / 嵌入式占位 |

## 模型名必须自己填写

正式配置和 example 配置都不会替你选择模型：

```yaml
profiles:
  qwen:
    roles:
      main:
        provider: qwen
        model: ""  # 必填：例如 qwen-plus
```

填好后再检查：

```bash
mini-agent config check --profile qwen
```

## API Key 策略

API Key 只能放在环境变量里，YAML 里只写环境变量名：

```yaml
api_key_env: DASHSCOPE_API_KEY
```

Windows PowerShell：

```powershell
$env:DASHSCOPE_API_KEY="你的 API Key"
```

Linux / ARM Linux：

```bash
export DASHSCOPE_API_KEY="你的 API Key"
```

`mini-agent config show` 会显示环境变量是否存在，但不会打印真实 Key。

## 国内模型

Qwen：

```yaml
profiles:
  qwen:
    roles:
      main:
        provider: qwen
        model: "qwen-plus"
```

DeepSeek：

```yaml
profiles:
  deepseek:
    roles:
      main:
        provider: deepseek
        model: "deepseek-chat"
```

## 本地模型

本地服务通常走 `local` provider：

```yaml
profiles:
  local:
    roles:
      main:
        provider: local
        model: "qwen2.5:7b"
```

如果本地服务地址不是 `http://localhost:11434/v1`，改 `providers.yaml`：

```yaml
profiles:
  local:
    providers:
      local:
        base_url: http://127.0.0.1:8000/v1
        api_key_env: ""
```

## 语音配置

STT/TTS 的 adapter 和模型写在 `models.yaml`：

```yaml
stt:
  adapter: dummy
tts:
  adapter: dummy
```

真实语音设备写在 `voice.yaml`：

```yaml
profiles:
  local:
    audio_input_device: ""
    audio_output_device: ""
```

默认 dummy 语音不需要麦克风，适合先跑通流程。

## 工具配置

`tools.yaml` 控制启用哪些内置技能：

```yaml
profiles:
  local:
    enabled: [calculator, get_time_local, tool_list, web_search, weather_open_meteo]
    allow_danger: false
```

默认联网能力是本地 safe skill：

- 标准 profile 默认启用 `web_search` 和 `weather_open_meteo`。
- `online` profile 额外启用 `fetch_url_text`。
- `minimal` 不默认启用联网。
- `edge` 只保留轻量 public-only 联网工具。

不要默认开启 `allow_danger: true`。详细说明见 [skills.md](skills.md)。

## MCP 配置

MCP 默认关闭，因为它可能联网、读写文件或执行命令。

默认联网不是 MCP：`web_search`、`fetch_url_text`、`weather_open_meteo` 是内置 safe skill。MCP 搜索只作为高级可选扩展，默认 disabled。

推荐分层：

- `minimal`：不启用 MCP。
- `online`：time、fetch、tavily_search、weather_open_meteo，以及可选 duckduckgo/free-search/one-search MCP。
- `dev`：github、filesystem、git、context7。
- `danger`：playwright、shell、docker。
- `edge`：time、fetch 占位。

查看 MCP 配置：

```bash
mini-agent mcp list --profile online
```

filesystem 必须配置 `sandbox`；shell/docker/playwright 必须保持 `risk_level: danger`。

## Demo 配置

`config/demo/` 保存可运行参考配置。它不是默认模板，只用于演示或复制参考。

## 推荐上手顺序

```bash
mini-agent init --profile local
# 先编辑 config/models.yaml，填写 local.main.model
mini-agent config show --profile local
mini-agent config check --profile local
mini-agent text --profile local
```

如果使用远程国内模型，把 `local` 换成 `qwen`、`deepseek`、`kimi`、`glm` 或 `siliconflow`，并设置对应 API Key 环境变量。
