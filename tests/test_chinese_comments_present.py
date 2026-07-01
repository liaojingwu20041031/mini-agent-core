from pathlib import Path


def test_example_config_contains_chinese_comment_keywords():
    files = [
        "models.yaml.example",
        "providers.yaml.example",
        "agent.yaml.example",
        "voice.yaml.example",
        "tools.yaml.example",
        "mcp.yaml.example",
    ]
    combined = "\n".join((Path("config") / name).read_text(encoding="utf-8") for name in files)

    for keyword in ["必填", "风险", "默认关闭"]:
        assert keyword in combined

