# 配置指南

`mini-agent-core` 的配置目标是：国内 AI 服务开箱可选、模型选择必须显式、密钥不进仓库、MCP 和危险工具默认关闭。

## 配置文件

运行时默认读取 `config/` 下的 6 个 YAML 文件：

```text
config/
  providers.yaml  # 覆盖或扩展 provider preset
  models.yaml     # 按 profile 和角色选择模型
  agent.yaml      # Agent loop、上下文长度、系统提示词
  voice.yaml      # STT/TTS/音频管线参数
  tools.yaml      # 内置工具启用列表和危险工具开关
  mcp.yaml        # MCP server 配置和风险等级
```

缺少文件时会提示从对应的 `.yaml.example` 复制，不会静默套用默认模型。这样做是为了避免误用高成本模型或把测试环境配置带到生产环境。

## Profile

`models.yaml`、`agent.yaml`、`voice.yaml`、`tools.yaml`、`mcp.yaml` 都支持 `profiles`：

```yaml
profiles:
  qwen:
    roles:
      main:
        provider: qwen
        model: qwen-plus
      stt:
        adapter: dummy
      tts:
        adapter: dummy
```

当前内置示例 profile：

- `local`：本地 OpenAI-compatible 服务，例如 Ollama、LM Studio、llama.cpp server、vLLM。
- `qwen`：阿里云百炼 / DashScope。
- `deepseek`：DeepSeek OpenAI-compatible API。
- `siliconflow`：硅基流动。
- `remote`：OpenAI 远程文本、STT、TTS 示例。
- `edge`：ARM / 嵌入式部署占位。

常用检查命令：

```bash
mini-agent config check --profile qwen
mini-agent config show --profile qwen
```

`config show` 只展示 API Key 环境变量名和是否存在，不打印真实密钥。

## Provider Preset

内置 provider preset 提供连接元信息：`base_url`、API Key 环境变量、别名和示例模型。preset 不会替你选择生产模型，模型必须在 `models.yaml` 或 `.env` 中显式声明。

| Provider | 常用别名 | API Key 环境变量 | 默认 base_url |
| --- | --- | --- | --- |
| `deepseek` | `ds` | `DEEPSEEK_API_KEY` | `https://api.deepseek.com` |
| `qwen` | `dashscope`, `aliyun`, `bailian`, `tongyi` | `DASHSCOPE_API_KEY` | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `kimi` | `moonshot` | `MOONSHOT_API_KEY` | `https://api.moonshot.cn/v1` |
| `glm` | `zhipu`, `bigmodel`, `zai` | `ZHIPUAI_API_KEY` | `https://open.bigmodel.cn/api/paas/v4` |
| `siliconflow` | `sf`, `guiji`, `silicon` | `SILICONFLOW_API_KEY` | `https://api.siliconflow.cn/v1` |
| `local` | `ollama`, `lmstudio`, `llama_cpp`, `vllm` | `LOCAL_LLM_API_KEY` | `http://localhost:11434/v1` |
| `custom` | `compatible` | `LLM_API_KEY` | 由 `LLM_BASE_URL` 指定 |

查看当前 provider preset：

```bash
python examples/provider_quickstart.py
```

阿里云百炼如果需要海外区域，可设置 region 为 `us` / `virginia`，会切到 `https://dashscope-us.aliyuncs.com/compatible-mode/v1`。

## 密钥策略

推荐使用厂商专属环境变量：

```env
DEEPSEEK_API_KEY=sk-...
DASHSCOPE_API_KEY=sk-...
MOONSHOT_API_KEY=sk-...
ZHIPUAI_API_KEY=sk-...
SILICONFLOW_API_KEY=sk-...
```

不要把真实 Key 写进 YAML。YAML 中只保留 `api_key_env`：

```yaml
main:
  provider: deepseek
  model: deepseek-v4-flash
  api_key_env: DEEPSEEK_API_KEY
```

`.env.example` 只用于展示变量名；本地真实 `.env` 应该保持未提交。

## `.env` 兼容入口

旧项目或简单 demo 可以继续用 `.env`：

```env
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-v4-flash
DEEPSEEK_API_KEY=sk-...
LLM_TIMEOUT=30
LLM_TEMPERATURE=0.2
LLM_EXTRA_BODY_JSON={"top_p":0.8}
LLM_ENABLE_THINKING=false
```

优先级要点：

- 显式 `LLM_BASE_URL` 优先于 provider preset 的 `base_url`。
- `LLM_MODEL` 必须显式设置；provider preset 只给示例模型。
- `LLM_API_KEY` 可用于 custom provider，国内厂商更推荐使用专属变量。

## 角色模型

`models.yaml` 按角色组织能力：

- `main`：主对话模型。
- `small`：轻量任务模型，可用于分类、摘要、规划等低成本任务。
- `embedding`：向量模型预留。
- `stt`：语音转文字 adapter。
- `tts`：文字转语音 adapter。

本地开发可以这样配置：

```yaml
profiles:
  local:
    roles:
      main:
        provider: local
        model: qwen2.5:7b
        base_url: http://localhost:11434/v1
      small:
        provider: local
        model: qwen2.5:1.5b
      stt:
        adapter: dummy
      tts:
        adapter: dummy
```

## 工具和 MCP 安全

`tools.yaml` 默认只启用 safe 工具。`confirm` 工具需要显式启用并通过确认回调；`danger` 工具默认不注册，执行时还需要 `ToolGuard(allow_danger=True)`。

`mcp.yaml` 默认关闭高风险能力：

- `filesystem` 需要配置 `sandbox`。
- `playwright`、`shell`、`docker`、`email`、`calendar`、`database_write` 这类能力默认视为高风险。
- V0.1 只提供配置校验、进程封装和 ToolDefinition bridge；真实 `tools/list`、`tools/call` 作为后续扩展点。

## 推荐上手顺序

1. 复制并编辑 `config/*.yaml.example`，或直接使用仓库里的示例 `config/*.yaml`。
2. 选择一个 profile，例如 `qwen`、`deepseek`、`local`。
3. 设置对应环境变量，例如 `DASHSCOPE_API_KEY` 或 `DEEPSEEK_API_KEY`。
4. 运行 `mini-agent config check --profile <name>`。
5. 运行 `python examples/text_<provider>_demo.py` 或在代码中调用 `OpenAICompatibleClient.from_provider(...)`。

