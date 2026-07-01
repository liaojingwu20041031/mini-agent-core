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

`main.model is required`：

```text
说明 config/models.yaml 的当前 profile 没填 main.model。
```

解决：填写模型名，例如：

```yaml
model: "qwen-plus"
```

`environment variable DASHSCOPE_API_KEY is not set`：

```powershell
$env:DASHSCOPE_API_KEY="你的 API Key"
```

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