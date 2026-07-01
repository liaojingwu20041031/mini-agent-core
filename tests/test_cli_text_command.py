from pathlib import Path

from mini_agent import cli


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
    (root / "agent.yaml").write_text(
        "profiles:\n  local:\n    max_steps: 1\n    system_prompt: test\n",
        encoding="utf-8",
    )
    (root / "voice.yaml").write_text("profiles:\n  local: {}\n", encoding="utf-8")
    (root / "tools.yaml").write_text(
        "profiles:\n  local:\n    enabled: [calculator]\n    allow_danger: false\n",
        encoding="utf-8",
    )
    (root / "mcp.yaml").write_text("profiles:\n  local:\n    servers: {}\n", encoding="utf-8")


def test_text_command_constructs_agent(tmp_path, monkeypatch):
    _write_config(tmp_path)
    called = {"run": False}

    def fake_run(self):
        called["run"] = True
        assert self.agent.llm.model == "test-model"

    monkeypatch.setattr(cli.TextCLI, "run", fake_run)

    assert cli.main(["text", "--config-dir", str(tmp_path), "--profile", "local"]) == 0
    assert called["run"] is True

