# Agent 与扩展

## Agent 配置

`config/agents.yaml` 只描述 Agent 身份、角色、能力、边界、风格、工具策略和项目上下文，不写模型名、API Key 或 base_url。

```yaml
agents:
  default:
    name: MiniAgent
    role: 通用轻量任务助手
    identity: 你是一个可嵌入项目的轻量 Agent Core。
    capabilities: [解释配置, 拆解任务, 调用 safe 工具]
    boundaries: [不保存密钥, 不绕过 danger 限制]
```

运行时优先使用 `agents.yaml` 拼接 system prompt；缺失时回退 `config/agent.yaml` 的 fallback `system_prompt`。

## 工具元信息

`@tool` 兼容旧写法，也支持 metadata：

```python
from mini_agent.core.tools import tool

@tool(
    description="Read project status.",
    title="读取项目状态",
    category="project",
    tags=("status",),
    when_to_use="需要查询只读状态时。",
    examples=("project_status()",),
)
def project_status() -> dict:
    return {"ok": True}
```

查看工具说明：

```powershell
mini-agent tools describe project_status --profile local
```

## ToolPack

```python
from mini_agent.extensions.base import ToolPack

def build_project_toolpack() -> ToolPack:
    return ToolPack(
        name="project.tools",
        description="项目工具包",
        tools=[project_status],
    )
```

`config/tools.yaml`：

```yaml
extensions:
  - module: project_tools
    factory: build_project_toolpack
```

外部模块加载失败会输出清晰错误，不影响基础工具运行。

## Capability

`Capability` 用来描述一组 ToolPack 和可选 Agent 指令，适合 APP、Web、机器人项目做能力包规划。当前实现保持轻量，不强制 entry_points。
