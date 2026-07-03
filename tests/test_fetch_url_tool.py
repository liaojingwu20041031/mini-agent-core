from mini_agent.skills.builtin.web import fetch_url_text


class FakeResponse:
    def __init__(self, text="", content=None, status_code=200, headers=None, url="https://example.com"):
        self.text = text
        self.content = content if content is not None else text.encode()
        self.status_code = status_code
        self.headers = headers or {"content-type": "text/html"}
        self.url = url
        self.encoding = "utf-8"


def _public_dns(monkeypatch):
    monkeypatch.setattr("mini_agent.skills.builtin.url_security.socket.getaddrinfo", lambda *args, **kwargs: [(None, None, None, None, ("93.184.216.34", 0))])


def test_fetch_url_text_cleans_html(monkeypatch):
    _public_dns(monkeypatch)
    html = "<html><head><title>T</title><script>x()</script></head><body><nav>N</nav><main>Hello world</main></body></html>"
    monkeypatch.setattr("mini_agent.skills.builtin.web.httpx.get", lambda *args, **kwargs: FakeResponse(html))

    result = fetch_url_text("https://example.com")

    assert result["ok"] is True
    assert result["title"] == "T"
    assert "Hello world" in result["text"]
    assert "x()" not in result["text"]


def test_fetch_url_text_truncates(monkeypatch):
    _public_dns(monkeypatch)
    monkeypatch.setattr("mini_agent.skills.builtin.web.httpx.get", lambda *args, **kwargs: FakeResponse("a" * 100, headers={"content-type": "text/plain"}))

    result = fetch_url_text("https://example.com", max_chars=10)

    assert result["ok"] is True
    assert result["text"] == "a" * 10
    assert result["truncated"] is True


def test_fetch_url_text_non_2xx(monkeypatch):
    _public_dns(monkeypatch)
    monkeypatch.setattr("mini_agent.skills.builtin.web.httpx.get", lambda *args, **kwargs: FakeResponse("no", status_code=403))

    result = fetch_url_text("https://example.com")

    assert result["ok"] is False
    assert result["error"]["code"] == "http_error"


def test_fetch_url_text_rejects_content_type(monkeypatch):
    _public_dns(monkeypatch)
    monkeypatch.setattr("mini_agent.skills.builtin.web.httpx.get", lambda *args, **kwargs: FakeResponse("bin", headers={"content-type": "image/png"}))

    result = fetch_url_text("https://example.com")

    assert result["ok"] is False
    assert result["error"]["code"] == "unsupported_content_type"
