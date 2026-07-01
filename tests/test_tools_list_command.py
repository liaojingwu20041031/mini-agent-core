from pathlib import Path

from mini_agent.cli import main


def _write_config(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "providers.yaml").write_text("profiles:\n  local:\n    providers: {}\n", encoding="utf-8")
    (root / "models.yaml").write_text(
        "profiles:\n  local:\n    roles:\n      main:\n        provider: local\n        model: test-model\n",
        encoding="utf-8",
    )
    (root / "agent.yaml").write_text("profiles:\n  local: {}\n", encoding="utf-8")
    (root / "voice.yaml").write_text("profiles:\n  local: {}\n", encoding="utf-8")
    (root / "tools.yaml").write_text(
        "profiles:\n  local:\n    enabled: [calculator, tool_list]\n    allow_danger: false\n",
        encoding="utf-8",
    )
    (root / "mcp.yaml").write_text("profiles:\n  local:\n    servers: {}\n", encoding="utf-8")


def test_tools_list_outputs_skills(tmp_path, capsys):
    _write_config(tmp_path)

    assert main(["tools", "list", "--config-dir", str(tmp_path), "--profile", "local"]) == 0

    output = capsys.readouterr().out
    assert "calculator" in output
    assert "safe" in output

