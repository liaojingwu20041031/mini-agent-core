from mini_agent.skills.builtin.confirm import http_post_json_confirm
from mini_agent.skills.builtin.web import fetch_url_text_public


def test_http_post_json_confirm_blocks_private_urls(monkeypatch):
    called = False

    def fake_post(*args, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr("httpx.post", fake_post)

    result = http_post_json_confirm("http://169.254.169.254/latest/meta-data", {"hello": "world"})

    assert result["ok"] is False
    assert result["error"]["code"] == "blocked_private_url"
    assert called is False


def test_fetch_url_text_public_blocks_domain_resolving_to_private_ip(monkeypatch):
    monkeypatch.setattr("mini_agent.skills.builtin.url_security.socket.getaddrinfo", lambda *args, **kwargs: [(None, None, None, None, ("127.0.0.1", 0))])

    result = fetch_url_text_public("https://example.com")

    assert result["ok"] is False
    assert result["error"]["code"] == "blocked_private_url"
