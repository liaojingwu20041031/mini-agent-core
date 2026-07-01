# mini-agent-core

`mini-agent-core` 是一个轻量 AI Agent 模板核心架构。它不是完整业务项目，也不是大而全 Agent 平台，而是一个可以快速植入机器人、APP、ARM Linux 开发板、Web 后台、桌面工具等项目的最小 Agent Kernel / SDK。

V0.1 的重点是：文本和语音交互共用同一个 `Agent`，工具调用有权限控制，LLM 统一走 OpenAI-compatible Chat Completions 接口，语音能力只做可插拔管线，不把重型模型或实时语音框架绑进核心。

## 项目结构

```text
mini_agent/
  core/          # Agent loop、LLM 边界、消息、工具、会话、权限、配置、trace
  interaction/   # text_cli、voice_cli
  voice/         # VoicePipeline 与音频/STT/TTS/VAD/wakeword 接口
  adapters/      # OpenAI-compatible、dummy STT/TTS、MCP/本地语音预留
  builtin_tools.py
examples/
tests/
edge/
```

## 安装与测试

```bash
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -e ".[dev]"
python -m pytest
```

## 文本模式

复制 `.env.example` 为 `.env`，配置 OpenAI-compatible 服务：

```env
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=你的 key
LLM_MODEL=gpt-4o-mini
LLM_TIMEOUT=30
AGENT_MAX_STEPS=5
```

运行：

```bash
python examples/text_chat_demo.py
```

CLI 命令：

- `/exit` 退出
- `/reset` 清空当前会话
- `/tools` 查看已注册工具

离线工具调用 demo：

```bash
python examples/text_tool_demo.py
```

## 语音模式

V0.1 默认提供 dummy STT/TTS，不需要麦克风、扬声器或语音模型：

```bash
python examples/voice_dummy_demo.py
```

语音流程是：

```text
AudioInput -> VAD/manual stop -> STT -> AgentCore -> TTS -> AudioOutput
```

`VoicePipeline` 只负责编排，不绕开 Agent 工具系统和权限系统。

## 注册工具

```python
from mini_agent.core.tools import ToolRegistry, tool

@tool(description="Read a sensor")
def read_sensor(name: str) -> dict:
    return {"name": name, "value": 42}

registry = ToolRegistry()
registry.register(read_sensor)
```

风险等级：

- `safe`：默认，可直接执行。
- `confirm`：必须提供 `confirm_callback` 且返回 True。
- `danger`：默认禁止，除非 `ToolGuard(allow_danger=True)`。

内置 mock 工具：

- `get_time()`
- `calculate(expression: str)`
- `get_system_status()`
- `read_mock_sensor(sensor_name: str)`
- `set_mock_led(state: str)`，`risk_level=confirm`
- `dangerous_shell(command: str)`，`risk_level=danger`，默认禁用

## 接 OpenAI-compatible 模型

`OpenAICompatibleClient` 使用 `/chat/completions`：

```python
from mini_agent.adapters.openai_compatible import OpenAICompatibleClient

llm = OpenAICompatibleClient(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model="qwen2.5:7b",
    timeout=30,
)
```

可接 OpenAI、OpenRouter、Ollama、llama.cpp server、vLLM、LM Studio、本地中转站等兼容服务。

## ARM / 嵌入式扩展

V0.1 不要求在 ARM 板上运行完整语音模型，但结构已按 ARM 部署预留：

- Agent Core 可以作为轻量 Python 服务运行。
- 本地 STT 可后续接 whisper.cpp 或 sherpa-onnx。
- 本地 TTS 可后续接 Piper 或 sherpa-onnx TTS。
- 硬件工具建议由 C++ Edge Runtime、HTTP、Unix Socket、ROS2 Service、串口网关暴露给 Agent。
- 模型路径、API 地址、音频设备都通过配置或环境变量传入，不写死 PC 路径。

`edge/cpp_tool_runtime` 是后续 C++ 低层工具运行时的占位结构。

## MCP 扩展

`mini_agent/adapters/mcp_adapter.py` 只保留边界。V0.1 不强依赖 MCP Python SDK，避免模板核心被 MCP 版本变化绑住。V0.2 可以把 MCP tool metadata 映射为本项目 `ToolDefinition`。

## 参考与本项目取舍

- smolagents：参考极简 Agent loop 和小抽象；本项目没有引入其框架。
- Mozilla tinyagent：参考轻依赖、callback、tracing、MCP 预留；本项目使用标准库 logging 和简单 adapter 边界实现。
- OpenAI Agents SDK：参考 Agent、Tools、Guardrails、VoicePipeline/Realtime/Voice 的概念边界；本项目只实现同步最小核心。
- Pipecat / LiveKit Agents：参考实时语音管线思想；V0.1 不作为依赖。
- whisper.cpp、sherpa-onnx、Piper：参考 ARM / 本地 STT/TTS 适配方向；V0.1 只预留 adapter。
- MCP Python SDK：参考工具协议方向；V0.1 不强绑定。

## V0.2 / V0.3 建议

V0.2：

- async/streaming Agent loop
- Responses API adapter
- MCP client adapter
- OpenTelemetry trace exporter
- sounddevice/webrtcvad 真实音频输入

V0.3：

- Realtime API adapter
- Pipecat/LiveKit bridge 示例
- ARM 部署脚本
- C++ Edge Runtime HTTP/Unix Socket 示例
- ROS2、串口、CAN、GPIO 工具适配模板

