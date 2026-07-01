import httpx
import pytest

from mini_agent.adapters.openai_compatible import OpenAICompatibleClient
from mini_agent.core.errors import AgentError
from mini_agent.core.messages import Message


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {"choices": [{"message": {"content": "ok"}}]}
        self.text = text
        self.request = httpx.Request("POST", "https://example.com/chat/completions")

    def raise_for_status(self):
        if self.status_code >= 400:
            response = httpx.Response(self.status_code, text=self.text, request=self.request)
            raise httpx.HTTPStatusError("error", request=self.request, response=response)

    def json(self):
        return self._payload


def test_openai_compatible_client_requires_explicit_model():
    with pytest.raises(ValueError, match="Model is required"):
        OpenAICompatibleClient.from_provider(provider="deepseek", api_key="key")


def test_openai_compatible_client_merges_extra_body(monkeypatch):
    captured = {}

    def fake_post(url, headers, json, timeout):
        captured.update({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return FakeResponse()

    monkeypatch.setattr(httpx, "post", fake_post)
    client = OpenAICompatibleClient.from_provider(
        provider="deepseek",
        api_key="key",
        model="explicit-model",
        extra_body={"top_p": 0.7, "thinking": {"type": "enabled"}},
    )

    response = client.chat([Message(role="user", content="hi")], timeout=9)

    assert response.content == "ok"
    assert captured["url"] == "https://api.deepseek.com/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer key"
    assert captured["json"]["model"] == "explicit-model"
    assert captured["json"]["top_p"] == 0.7
    assert captured["json"]["thinking"] == {"type": "enabled"}
    assert captured["timeout"] == 9


def test_openai_compatible_client_wraps_http_errors(monkeypatch):
    def fake_post(url, headers, json, timeout):
        return FakeResponse(status_code=429, text="rate limited")

    monkeypatch.setattr(httpx, "post", fake_post)
    client = OpenAICompatibleClient.from_provider(provider="qwen", api_key="key", model="explicit-test-model")

    with pytest.raises(AgentError) as exc:
        client.chat([Message(role="user", content="hi")])

    message = str(exc.value)
    assert "provider=qwen" in message
    assert "status=429" in message
    assert "rate limited" in message
