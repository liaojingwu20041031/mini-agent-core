"""Safe, keyless web tools."""

from __future__ import annotations

import html
import re
import time
from html.parser import HTMLParser
from typing import Any
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import httpx

from mini_agent.core.tools import tool
from mini_agent.skills.builtin.url_security import blocked_host as _blocked_host
from mini_agent.skills.builtin.url_security import validate_public_url as _validate_public_url

USER_AGENT = "mini-agent-core/0.1 (+https://github.com/liaojingwu20041031/mini-agent-core)"
MAX_SEARCH_RESULTS = 10
MAX_FETCH_BYTES = 1024 * 1024
MAX_PUBLIC_FETCH_BYTES = 500 * 1024
FETCH_ALLOWED_TYPES = ("text/html", "text/plain", "application/json")


class _DDGParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict[str, str]] = []
        self._in_title = False
        self._in_snippet = False
        self._current: dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key: value or "" for key, value in attrs}
        class_name = attrs_dict.get("class", "")
        if tag == "a" and ("result__a" in class_name or class_name == "result-link"):
            href = attrs_dict.get("href", "")
            self._current = {"title": "", "url": _normalize_ddg_url(href), "snippet": "", "source": "duckduckgo"}
            self._in_title = True
        elif self._current and ("result__snippet" in class_name or "result-snippet" in class_name):
            self._in_snippet = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._in_title:
            self._in_title = False
            if self._current and self._current["title"] and self._current["url"]:
                self.results.append(self._current)
            self._current = None
        if self._in_snippet and tag in {"a", "div", "span"}:
            self._in_snippet = False

    def handle_data(self, data: str) -> None:
        text = _clean_space(data)
        if not text or not self._current:
            return
        if self._in_title:
            self._current["title"] = _clean_space(self._current["title"] + " " + text)
        elif self._in_snippet:
            self._current["snippet"] = _clean_space(self._current["snippet"] + " " + text)


class _TextExtractor(HTMLParser):
    SKIP_TAGS = {"script", "style", "nav", "footer", "header", "noscript", "svg"}

    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.parts: list[str] = []
        self._skip_depth = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        text = _clean_space(data)
        if not text:
            return
        if self._in_title:
            self.title = _clean_space(self.title + " " + text)
            return
        if self._skip_depth:
            return
        self.parts.append(text)

    @property
    def text(self) -> str:
        return _clean_space(" ".join(self.parts))


def _clean_space(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(text or "")).strip()


def _normalize_ddg_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    if parsed.path.startswith("/l/"):
        uddg = parse_qs(parsed.query).get("uddg", [""])[0]
        return unquote(uddg) if uddg else url
    return url


def _error(started: float, code: str, message: str, **extra: Any) -> dict[str, Any]:
    return {
        "ok": False,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
        "error": {"code": code, "message": message},
        **extra,
    }


@tool(description="Search the public web with a lightweight keyless DuckDuckGo HTML parser.", timeout=12)
def web_search(query: str, max_results: int = 5, region: str = "wt-wt") -> dict[str, Any]:
    started = time.perf_counter()
    limit = max(1, min(int(max_results or 5), MAX_SEARCH_RESULTS))
    if not query.strip():
        return _error(started, "invalid_query", "query 不能为空", engine="duckduckgo", query=query, results=[])
    try:
        response = httpx.get(
            "https://duckduckgo.com/html/",
            params={"q": query, "kl": region},
            headers={"User-Agent": USER_AGENT},
            timeout=10,
            follow_redirects=True,
        )
        if response.status_code >= 400:
            return _error(
                started,
                "http_error",
                f"搜索请求失败：HTTP {response.status_code}",
                engine="duckduckgo",
                query=query,
                results=[],
            )
        parser = _DDGParser()
        parser.feed(response.text)
        results = parser.results[:limit]
    except httpx.TimeoutException:
        return _error(started, "timeout", "搜索请求超时", engine="duckduckgo", query=query, results=[])
    except httpx.HTTPError as exc:
        return _error(started, "http_error", str(exc), engine="duckduckgo", query=query, results=[])
    except Exception as exc:
        return _error(started, "parse_error", f"{type(exc).__name__}: {exc}", engine="duckduckgo", query=query, results=[])
    if not results:
        return _error(started, "empty_result", "没有解析到搜索结果", engine="duckduckgo", query=query, results=[])
    return {
        "ok": True,
        "engine": "duckduckgo",
        "query": query,
        "results": results,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
        "error": None,
        "note": "免费页面解析，稳定性不如商业搜索 API；请以结果来源页面为准。",
    }


@tool(description="Fetch public URL text safely. Blocks private network addresses and binary content.", timeout=15)
def fetch_url_text(url: str, max_chars: int = 6000) -> dict[str, Any]:
    started = time.perf_counter()
    clean_url, blocked = _validate_public_url(url)
    if blocked:
        return _error(started, blocked, f"URL 不允许访问：{blocked}", url=url, final_url="", text="")
    limit = max(1, min(int(max_chars or 6000), 20000))
    try:
        current_url = clean_url
        response = None
        for redirect_count in range(4):
            response = httpx.get(
                current_url,
                headers={"User-Agent": USER_AGENT},
                timeout=10,
                follow_redirects=False,
            )
            if response.status_code not in {301, 302, 303, 307, 308}:
                break
            location = response.headers.get("location", "")
            next_url = urljoin(current_url, location)
            clean_next_url, redirect_blocked = _validate_public_url(next_url)
            if redirect_blocked:
                return _error(started, redirect_blocked, f"重定向 URL 不允许访问：{redirect_blocked}", url=url, final_url=next_url, text="")
            if redirect_count == 3:
                return _error(started, "too_many_redirects", "重定向超过 3 次", url=url, final_url=next_url, text="")
            current_url = clean_next_url
        if response is None:
            return _error(started, "http_error", "没有收到响应", url=url, final_url="", text="")
        if response.status_code < 200 or response.status_code >= 300:
            return _error(started, "http_error", f"HTTP {response.status_code}", url=url, final_url=str(response.url), text="")
        content_type = response.headers.get("content-type", "").split(";")[0].lower()
        if content_type and content_type not in FETCH_ALLOWED_TYPES:
            return _error(started, "unsupported_content_type", content_type, url=url, final_url=str(response.url), text="")
        body = response.content
        if len(body) > MAX_FETCH_BYTES:
            body = body[:MAX_FETCH_BYTES]
        decoded = body.decode(response.encoding or "utf-8", errors="replace")
        if "html" in content_type or "<html" in decoded[:500].lower():
            parser = _TextExtractor()
            parser.feed(decoded)
            title = parser.title
            text = parser.text
        else:
            title = ""
            text = _clean_space(decoded)
    except httpx.TimeoutException:
        return _error(started, "timeout", "抓取网页超时", url=url, final_url="", text="")
    except httpx.HTTPError as exc:
        return _error(started, "http_error", str(exc), url=url, final_url="", text="")
    truncated = len(text) > limit
    return {
        "ok": True,
        "url": url,
        "final_url": str(response.url),
        "status_code": response.status_code,
        "content_type": content_type,
        "title": title,
        "text": text[:limit],
        "truncated": truncated,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
        "error": None,
    }


@tool(
    description="Fetch public HTTP/HTTPS text with private-network blocking and tight size limits.",
    title="抓取公开网页文本",
    category="web",
    tags=("web", "fetch", "public"),
    when_to_use="需要读取公开网页、纯文本或 JSON 的少量内容。",
    when_not_to_use="不要用于内网、localhost、云元数据地址、二进制下载或需要执行 JavaScript 的页面。",
    examples=("fetch_url_text_public(url='https://example.com')",),
    timeout=15,
)
def fetch_url_text_public(url: str, max_chars: int = 4000) -> dict[str, Any]:
    started = time.perf_counter()
    clean_url, blocked = _validate_public_url(url)
    if blocked:
        return _error(started, blocked, f"URL 不允许访问：{blocked}", url=url, final_url="", text="")
    limit = max(1, min(int(max_chars or 4000), 4000))
    try:
        current_url = clean_url
        response = None
        for redirect_count in range(4):
            response = httpx.get(
                current_url,
                headers={"User-Agent": USER_AGENT},
                timeout=10,
                follow_redirects=False,
            )
            if response.status_code not in {301, 302, 303, 307, 308}:
                break
            location = response.headers.get("location", "")
            next_url = urljoin(current_url, location)
            clean_next_url, redirect_blocked = _validate_public_url(next_url)
            if redirect_blocked:
                return _error(started, redirect_blocked, f"重定向 URL 不允许访问：{redirect_blocked}", url=url, final_url=next_url, text="")
            if redirect_count == 3:
                return _error(started, "too_many_redirects", "重定向超过 3 次", url=url, final_url=next_url, text="")
            current_url = clean_next_url
        if response is None:
            return _error(started, "http_error", "没有收到响应", url=url, final_url="", text="")
        if response.status_code < 200 or response.status_code >= 300:
            return _error(started, "http_error", f"HTTP {response.status_code}", url=url, final_url=str(response.url), text="")
        content_type = response.headers.get("content-type", "").split(";")[0].lower()
        if content_type and content_type not in FETCH_ALLOWED_TYPES:
            return _error(started, "unsupported_content_type", content_type, url=url, final_url=str(response.url), text="")
        body = response.content
        if len(body) > MAX_PUBLIC_FETCH_BYTES:
            body = body[:MAX_PUBLIC_FETCH_BYTES]
        decoded = body.decode(response.encoding or "utf-8", errors="replace")
        if "html" in content_type or "<html" in decoded[:500].lower():
            parser = _TextExtractor()
            parser.feed(decoded)
            title = parser.title
            text = parser.text
        else:
            title = ""
            text = _clean_space(decoded)
    except httpx.TimeoutException:
        return _error(started, "timeout", "抓取网页超时", url=url, final_url="", text="")
    except httpx.HTTPError as exc:
        return _error(started, "http_error", str(exc), url=url, final_url="", text="")
    truncated = len(text) > limit
    return {
        "ok": True,
        "url": url,
        "final_url": str(response.url),
        "status_code": response.status_code,
        "content_type": content_type,
        "title": title,
        "text": text[:limit],
        "truncated": truncated,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
        "error": None,
    }
