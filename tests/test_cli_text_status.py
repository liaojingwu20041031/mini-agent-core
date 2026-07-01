import builtins
from pathlib import Path

from mini_agent import cli
from mini_agent.core.llm import LLMResponse


def _write_config(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "providers.yaml").write_text(
        "profiles:\n  local:\n    providers:\n      local:\n        base_url: http://localhost:11434/v1\n        api_key_env: ''\n",
        encoding="utf-8",
    )
    (root / "models.yaml").write_text(
        "profiles:\n  local:\n    roles:\n      main:\n        provider: local\n        model: test-model\n",
        encoding="utf-8",
    )
    (root / "agent.yaml").write_text("profiles:\n  local:\n    max_steps: 1\n", encoding="utf-8")
    (root / "voice.yaml").write_text("profiles:\n  local: {}\n", encoding="utf-8")
    (root / "tools.yaml").write_text("profiles:\n  local:\n    enabled: [calculator]\n    allow_danger: false\n", encoding="utf-8")
    (root / "mcp.yaml").write_text("profiles:\n  local:\n    servers: {}\n", encoding="utf-8")


def _fake_chat(self, messages, tools=None, timeout=None):
    return LLMResponse(content="ok")


def test_text_cli_shows_status_by_default(tmp_path, monkeypatch, capsys):
    _write_config(tmp_path)
    inputs = iter(["hi", "/exit"])
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs))
    monkeypatch.setattr("mini_agent.adapters.openai_compatible.OpenAICompatibleClient.chat", _fake_chat)

    assert cli.main(["text", "--config-dir", str(tmp_path), "--profile", "local"]) == 0

    output = capsys.readouterr().out
    assert "[llm] 请求中" in output
    assert "[llm] 完成" in output


def test_text_cli_no_status_hides_status(tmp_path, monkeypatch, capsys):
    _write_config(tmp_path)
    inputs = iter(["hi", "/exit"])
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs))
    monkeypatch.setattr("mini_agent.adapters.openai_compatible.OpenAICompatibleClient.chat", _fake_chat)

    assert cli.main(["text", "--config-dir", str(tmp_path), "--profile", "local", "--no-status"]) == 0

    output = capsys.readouterr().out
    assert "[llm]" not in output
