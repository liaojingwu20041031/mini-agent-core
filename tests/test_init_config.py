from pathlib import Path

from mini_agent.cli import main


def _write_examples(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for name in ["providers", "models", "agent", "voice", "tools", "mcp"]:
        (root / f"{name}.yaml.example").write_text(f"profiles:\n  local: {{}}\n# 必填 默认关闭 风险\n", encoding="utf-8")
    (root / "quickstart.yaml.example").write_text("# 必填 默认关闭 风险\nprofile: local\n", encoding="utf-8")


def test_init_config_copies_examples(tmp_path):
    _write_examples(tmp_path)

    assert main(["init", "--config-dir", str(tmp_path), "--profile", "local"]) == 0

    assert (tmp_path / "models.yaml").exists()
    assert (tmp_path / "quickstart.yaml").exists()


def test_init_config_does_not_overwrite_existing(tmp_path):
    _write_examples(tmp_path)
    target = tmp_path / "models.yaml"
    target.write_text("keep: true\n", encoding="utf-8")

    assert main(["init", "--config-dir", str(tmp_path), "--profile", "local"]) == 0

    assert target.read_text(encoding="utf-8") == "keep: true\n"


def test_init_qwen_explains_dashscope_env(tmp_path, capsys):
    _write_examples(tmp_path)

    assert main(["init", "--config-dir", str(tmp_path), "--profile", "qwen"]) == 0

    output = capsys.readouterr().out
    assert "DASHSCOPE_API_KEY" in output
    assert "QWEN_API_KEY 不是默认变量名" in output
    assert "--profile deepseek" in output
