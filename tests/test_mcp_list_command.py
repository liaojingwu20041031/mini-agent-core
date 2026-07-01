from mini_agent.cli import main


def test_mcp_list_outputs_servers(tmp_path, capsys):
    (tmp_path / "mcp.yaml").write_text(
        "profiles:\n"
        "  online:\n"
        "    servers:\n"
        "      fetch:\n"
        "        enabled: false\n"
        "        transport: stdio\n"
        "        command: fetch-mcp\n"
        "        risk_level: safe\n",
        encoding="utf-8",
    )

    assert main(["mcp", "list", "--config-dir", str(tmp_path), "--profile", "online"]) == 0

    output = capsys.readouterr().out
    assert "fetch" in output
    assert "fetch-mcp" in output
    assert "safe" in output

