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


def test_text_command_validates_selected_profile(tmp_path, capsys, monkeypatch):
    _write_config(tmp_path)
    models = (
        "profiles:\n"
        "  local:\n"
        "    roles:\n"
        "      main:\n"
        "        provider: local\n"
        "        model: test-model\n"
        "  deepseek:\n"
        "    roles:\n"
        "      main:\n"
        "        provider: deepseek\n"
        "        model: ''\n"
    )
    (tmp_path / "models.yaml").write_text(models, encoding="utf-8")
    (tmp_path / "providers.yaml").write_text(
        "profiles:\n"
        "  local:\n"
        "    providers:\n"
        "      local:\n"
        "        base_url: http://localhost:11434/v1\n"
        "        api_key_env: ''\n"
        "  deepseek:\n"
        "    providers: {}\n",
        encoding="utf-8",
    )
    for name in ["agent", "voice", "tools", "mcp"]:
        data = (tmp_path / f"{name}.yaml").read_text(encoding="utf-8")
        (tmp_path / f"{name}.yaml").write_text(data + "\n  deepseek: {}\n", encoding="utf-8")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")

    assert cli.main(["text", "--config-dir", str(tmp_path), "--profile", "deepseek"]) == 1

    output = capsys.readouterr().out
    assert "启动文本模式失败：profile 'deepseek' 配置未通过检查" in output
    assert "main.model 必填" in output
    assert "mini-agent config check --profile deepseek" in output
