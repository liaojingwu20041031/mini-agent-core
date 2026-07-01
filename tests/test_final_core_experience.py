import json
import sys
from pathlib import Path

import yaml

from mini_agent import cli
from mini_agent.core.agent_spec import AgentSpecConfig, load_agent_spec
from mini_agent.core.state import load_state
from mini_agent.skills.registry import build_tool_registry
from mini_agent.toolpacks.ros2_stub import build_ros2_stub_toolpack


BANNED_CLI_MODELS = [
    "qwen" + "-plus",
    "deepseek" + "-chat",
    "deepseek" + "-reasoner",
    "kimi" + "-k2.6",
    "glm" + "-4.5",
    "gpt" + "-4o-mini",
    "qwen" + "2.5:7b",
    "llama" + "3.1:8b",
    "DeepSeek" + "-V3.1",
    "edge" + "-model",
]


def _write_config(root: Path, model: str = "") -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "providers.yaml").write_text(
        "profiles:\n  local:\n    providers:\n      local:\n        base_url: http://localhost:11434/v1\n        api_key_env: ''\n",
        encoding="utf-8",
    )
    (root / "models.yaml").write_text(
        f"profiles:\n  local:\n    roles:\n      main:\n        provider: local\n        model: {model!r}\n",
        encoding="utf-8",
    )
    (root / "agent.yaml").write_text("profiles:\n  local:\n    max_steps: 1\n    system_prompt: fallback\n", encoding="utf-8")
    (root / "voice.yaml").write_text("profiles:\n  local: {}\n", encoding="utf-8")
    (root / "tools.yaml").write_text(
        "profiles:\n  local:\n    tools:\n      enabled: [calculator, web_search, fetch_url_text_public]\n    allow_danger: false\n",
        encoding="utf-8",
    )
    (root / "mcp.yaml").write_text("profiles:\n  local:\n    servers: {}\n", encoding="utf-8")


def test_cli_does_not_hardcode_model_names():
    text = Path("mini_agent/cli.py").read_text(encoding="utf-8")
    for model_id in BANNED_CLI_MODELS:
        assert model_id not in text


def test_docs_do_not_default_to_vendor_profile_in_core_flow():
    docs = "\n".join(
        Path(path).read_text(encoding="utf-8")
        for path in ["README.md", "docs/快速开始.md", "docs/配置指南.md"]
    )
    for command in [
        "init --profile " + "qwen",
        "models list --profile " + "qwen",
        "models use --profile " + "qwen",
        "config check --profile " + "qwen",
        "use --profile " + "qwen",
        "config where --profile " + "qwen",
        "config show --profile " + "qwen",
    ]:
        assert command not in docs
    assert "init --profile <profile>" in docs
    assert "$env:<API_KEY_ENV>" in docs
    assert "OpenAI-compatible 服务" in docs


def test_docs_show_key_or_local_service_before_models_list():
    for path in ["README.md", "docs/快速开始.md"]:
        text = Path(path).read_text(encoding="utf-8")
        key_index = text.index("$env:<API_KEY_ENV>")
        local_index = text.index("OpenAI-compatible 服务")
        list_index = text.index("mini-agent models list --profile <profile>")
        assert key_index < list_index
        assert local_index < list_index


def test_models_list_and_use_roundtrip(tmp_path, monkeypatch, capsys):
    _write_config(tmp_path)

    class Response:
        status_code = 200
        text = ""

        def json(self):
            return {"data": [{"id": "server-model-a"}, {"id": "server-model-b"}]}

    monkeypatch.setattr("httpx.get", lambda *args, **kwargs: Response())

    assert cli.main(["models", "list", "--config-dir", str(tmp_path), "--profile", "local"]) == 0
    output = capsys.readouterr().out
    assert "server-model-a" in output
    assert "model config path" in output

    assert cli.main(["models", "use", "--config-dir", str(tmp_path), "--profile", "local", "--model", "server-model-b"]) == 0
    data = yaml.safe_load((tmp_path / "models.yaml").read_text(encoding="utf-8"))
    assert data["profiles"]["local"]["roles"]["main"]["model"] == "server-model-b"


def test_models_check_config_where_and_show_hide_model(tmp_path, capsys):
    _write_config(tmp_path, model="private-user-model")

    assert cli.main(["models", "check", "--config-dir", str(tmp_path), "--profile", "local"]) == 0
    assert cli.main(["config", "where", "--config-dir", str(tmp_path), "--profile", "local", "--role", "main"]) == 0
    assert cli.main(["config", "show", "--config-dir", str(tmp_path), "--profile", "local"]) == 0
    output = capsys.readouterr().out
    assert "profiles.local.roles.main.model" in output
    assert "private-user-model" not in output
    assert "<已配置>" in output

    assert cli.main(["config", "show", "--config-dir", str(tmp_path), "--profile", "local", "--show-model"]) == 0
    assert "private-user-model" in capsys.readouterr().out


def test_use_state_does_not_store_sensitive_fields(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / "config"
    _write_config(config_dir, model="private-user-model")

    assert cli.main(["use", "--config-dir", str(config_dir), "--profile", "local", "--agent", "default"]) == 0
    state = load_state(tmp_path)
    assert state.default_profile == "local"
    raw = json.loads((tmp_path / ".mini-agent" / "state.json").read_text(encoding="utf-8"))
    assert set(raw) == {"default_profile", "default_agent", "default_mode", "config_dir"}
    assert "private-user-model" not in json.dumps(raw)


def test_agent_spec_loads_and_builds_prompt(tmp_path):
    (tmp_path / "agents.yaml").write_text(
        "agents:\n"
        "  robot:\n"
        "    name: RobotAgent\n"
        "    role: 巡检\n"
        "    identity: 上层任务协调者\n"
        "    capabilities: [查询状态]\n"
        "    boundaries: [不做实时控制]\n",
        encoding="utf-8",
    )
    spec = load_agent_spec(tmp_path, "robot")
    prompt = spec.to_system_prompt()
    assert "RobotAgent" in prompt
    assert "不做实时控制" in prompt


def test_tools_metadata_describe_and_toolpack_extension(tmp_path, monkeypatch, capsys):
    _write_config(tmp_path, model="test-model")
    assert cli.main(["tools", "describe", "fetch_url_text_public", "--config-dir", str(tmp_path), "--profile", "local"]) == 0
    output = capsys.readouterr().out
    assert "when_not_to_use" in output

    module_path = tmp_path / "project_tools.py"
    module_path.write_text(
        "from mini_agent.extensions.base import ToolPack\n"
        "from mini_agent.core.tools import tool\n"
        "@tool(description='Demo external tool')\n"
        "def external_demo(): return 'ok'\n"
        "def build_pack(): return ToolPack(name='project.demo', description='demo', tools=[external_demo])\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    registry = build_tool_registry([])
    from mini_agent.extensions.loader import load_external_toolpack

    load_external_toolpack({"module": "project_tools", "factory": "build_pack"}).register(registry)
    assert registry.get("external_demo") is not None


def test_ros2_stub_has_no_rclpy_and_danger_not_default():
    assert "rclpy" not in sys.modules
    pack = build_ros2_stub_toolpack()
    names = {getattr(tool, "__mini_agent_tool__").name for tool in pack.tools}
    risks = {getattr(tool, "__mini_agent_tool__").name: getattr(tool, "__mini_agent_tool__").risk_level for tool in pack.tools}
    assert "send_velocity_command" not in names
    assert risks["save_map"] == "confirm"
    assert risks["send_patrol_route"] == "confirm"
