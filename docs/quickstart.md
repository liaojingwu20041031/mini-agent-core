# 快速开始

这份教程面向第一次使用 `mini-agent-core` 的用户。命令尽量完整，先跑通，再慢慢改。

## Windows 安装方式

```powershell
cd "D:\E_kaifawenjian\AI Agent\mini-agent-core"
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -e ".[dev]"
mini-agent --help
```

## Linux / ARM Linux 安装方式

```bash
cd mini-agent-core
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
mini-agent --help
```

## 选择模型 profile

`mini-agent-core` 不默认绑定任何一家模型厂商。你先选择 profile，再填写对应的模型名和环境变量：

| 场景 | profile | API Key 环境变量 | 模型名示例 |
| --- | --- | --- | --- |
| 本地 Ollama / LM Studio / llama.cpp | `local` | 通常不需要 | `qwen2.5:7b` |
| 阿里云百炼 / DashScope | `qwen` | `DASHSCOPE_API_KEY` | `qwen-plus` |
| DeepSeek | `deepseek` | `DEEPSEEK_API_KEY` | `deepseek-chat` |
| Moonshot Kimi | `kimi` | `MOONSHOT_API_KEY` | `kimi-k2.6` |
| 智谱 GLM | `glm` | `ZHIPUAI_API_KEY` | `glm-4.5` |
| 硅基流动 | `siliconflow` | `SILICONFLOW_API_KEY` | `deepseek-ai/DeepSeek-V3.1` |

初始化命令里的 `--profile` 可以换成上表任意一个，下面只用 DeepSeek 做命令示例：

```bash
mini-agent init --profile deepseek
```

## 使用本地 Ollama / LM Studio / llama.cpp server

先启动你的本地 OpenAI-compatible 服务，例如 Ollama：

```bash
ollama serve
```

初始化配置：

```bash
mini-agent init --profile local
```

编辑 `config/models.yaml`：

```yaml
profiles:
  local:
    roles:
      main:
        provider: local
        model: "qwen2.5:7b"
```

检查并启动：

```bash
mini-agent config check --profile local
mini-agent text --profile local
```

## 使用 Qwen

Windows PowerShell：

```powershell
mini-agent init --profile qwen
$env:DASHSCOPE_API_KEY="你的 API Key"
```

Linux / ARM Linux：

```bash
mini-agent init --profile qwen
export DASHSCOPE_API_KEY="你的 API Key"
```

编辑 `config/models.yaml`：

```yaml
profiles:
  qwen:
    roles:
      main:
        provider: qwen
        model: "qwen-plus"
```

运行：

```bash
mini-agent config check --profile qwen
mini-agent text --profile qwen
```

联网实测：

```text
> 搜索一下 mini-agent-core 是什么
> 查询武汉今天的天气
```

确认当前 profile 启用了哪些工具：

```bash
mini-agent tools list --profile qwen
```

## 使用 DeepSeek

Windows PowerShell：

```powershell
mini-agent init --profile deepseek
$env:DEEPSEEK_API_KEY="你的 API Key"
```

Linux / ARM Linux：

```bash
mini-agent init --profile deepseek
export DEEPSEEK_API_KEY="你的 API Key"
```

编辑 `config/models.yaml`：

```yaml
profiles:
  deepseek:
    roles:
      main:
        provider: deepseek
        model: "deepseek-chat"
```

运行：

```bash
mini-agent config check --profile deepseek
mini-agent text --profile deepseek
```

## 使用 dummy 语音模式

dummy 语音模式用文字模拟语音输入输出，不需要麦克风：

```bash
mini-agent voice --profile local
```

如果 `local.main.model` 还没填，先按本地模型章节填写模型名。

## 状态显示

文本模式默认显示简洁状态，方便确认模型和工具正在运行：

```bash
mini-agent text --profile qwen
```

如果你要嵌入其它系统，想关闭控制台状态：

```bash
mini-agent text --profile qwen --no-status
```

调试底层日志时再开启：

```bash
mini-agent text --profile qwen --debug
```

## 注册第一个工具

```python
from mini_agent.core.tools import ToolRegistry, tool

@tool(description="读取一个模拟传感器")
def read_sensor(name: str) -> dict:
    return {"name": name, "value": 42}

registry = ToolRegistry()
registry.register(read_sensor)
print(registry.list()[0].name)
```

## 常见错误排查

`main.model 必填`：

```text
说明 config/models.yaml 的当前 profile 没填 main.model。
```

解决：填写模型名，例如：

```yaml
model: "deepseek-chat"
```

`environment variable XXX_API_KEY is not set`：

```powershell
$env:DEEPSEEK_API_KEY="你的 API Key"
```

把 `DEEPSEEK_API_KEY` 替换为你当前 profile 对应的环境变量，例如 `DASHSCOPE_API_KEY`、`MOONSHOT_API_KEY`、`ZHIPUAI_API_KEY` 或 `SILICONFLOW_API_KEY`。

`Unknown profile`：

```bash
mini-agent config show --profile local
```

确认 `config/*.yaml` 里是否都有这个 profile。

本地模型连不上：

```bash
curl http://localhost:11434/v1/models
```

确认 base_url、端口和本地服务是否启动。

profile 混用：

```text
如果你运行 mini-agent config check --profile qwen，只代表 qwen 有效。
再运行 mini-agent text --profile deepseek 时，deepseek 仍然需要单独填写模型名和 API Key。
```

联网工具失败：

```text
web_search 返回 timeout / empty_result / http_error 时，说明免费搜索页解析失败或网络不可达。
fetch_url_text 返回 blocked_private_url 时，说明目标是内网或解析到了私有 IP。
weather_open_meteo 返回 city_not_found 时，说明 Open-Meteo 没找到该城市。
```
