from mini_agent.skills.builtin.web import fetch_url_text


def test_fetch_url_blocks_bad_schemes():
    assert fetch_url_text("file:///etc/passwd")["error"]["code"] == "unsupported_scheme"
    assert fetch_url_text("ftp://example.com/a")["error"]["code"] == "unsupported_scheme"


def test_fetch_url_blocks_localhost():
    assert fetch_url_text("http://localhost")["error"]["code"] == "blocked_private_url"


def test_fetch_url_blocks_private_ips(monkeypatch):
    private_ips = ["127.0.0.1", "10.0.0.1", "172.16.0.1", "192.168.1.1", "169.254.169.254"]
    for ip in private_ips:
        result = fetch_url_text(f"http://{ip}")
        assert result["ok"] is False
        assert result["error"]["code"] == "blocked_private_url"


def test_fetch_url_blocks_domain_resolving_to_private_ip(monkeypatch):
    monkeypatch.setattr("mini_agent.skills.builtin.url_security.socket.getaddrinfo", lambda *args, **kwargs: [(None, None, None, None, ("10.0.0.1", 0))])

    result = fetch_url_text("https://example.com")

    assert result["ok"] is False
    assert result["error"]["code"] == "blocked_private_url"
