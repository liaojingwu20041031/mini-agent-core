import httpx

from mini_agent.skills.builtin.web import web_search


class FakeResponse:
    def __init__(self, text="", status_code=200):
        self.text = text
        self.status_code = status_code


def test_web_search_parses_results(monkeypatch):
    html = """
    <a class="result__a" href="https://example.com/a">Example A</a>
    <a class="result__snippet">Snippet A</a>
    <a class="result__a" href="/l/?uddg=https%3A%2F%2Fexample.com%2Fb">Example B</a>
    """
    monkeypatch.setattr("mini_agent.skills.builtin.web.httpx.get", lambda *args, **kwargs: FakeResponse(html))

    result = web_search("mini-agent-core", max_results=20)

    assert result["ok"] is True
    assert len(result["results"]) <= 10
    assert result["results"][0]["title"] == "Example A"
    assert result["results"][1]["url"] == "https://example.com/b"


def test_web_search_timeout(monkeypatch):
    def raise_timeout(*args, **kwargs):
        raise httpx.TimeoutException("timeout")

    monkeypatch.setattr("mini_agent.skills.builtin.web.httpx.get", raise_timeout)

    result = web_search("x")

    assert result["ok"] is False
    assert result["error"]["code"] == "timeout"


def test_web_search_empty_result(monkeypatch):
    monkeypatch.setattr("mini_agent.skills.builtin.web.httpx.get", lambda *args, **kwargs: FakeResponse("<html></html>"))

    result = web_search("x")

    assert result["ok"] is False
    assert result["error"]["code"] == "empty_result"
