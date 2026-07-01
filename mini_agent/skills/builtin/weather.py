"""Safe weather tools backed by Open-Meteo."""

from __future__ import annotations

import time
from typing import Any

import httpx

from mini_agent.core.tools import tool

USER_AGENT = "mini-agent-core/0.1"


def _error(started: float, code: str, message: str, **extra: Any) -> dict[str, Any]:
    return {
        "ok": False,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
        "error": {"code": code, "message": message},
        **extra,
    }


@tool(description="Get current weather by city from Open-Meteo free APIs.", timeout=12)
def weather_open_meteo(city: str, country_code: str = "", language: str = "zh") -> dict[str, Any]:
    started = time.perf_counter()
    if not city.strip():
        return _error(started, "invalid_city", "city 不能为空", city=city, source="open-meteo")
    try:
        geo = httpx.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 5, "language": language, "format": "json"},
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        if geo.status_code >= 400:
            return _error(started, "http_error", f"Geocoding HTTP {geo.status_code}", city=city, source="open-meteo")
        candidates = geo.json().get("results") or []
        if country_code:
            expected = country_code.upper()
            candidates = [item for item in candidates if str(item.get("country_code", "")).upper() == expected]
        if not candidates:
            return _error(started, "city_not_found", "没有找到城市", city=city, source="open-meteo")
        place = candidates[0]
        forecast = httpx.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m,wind_speed_10m,weather_code",
                "timezone": "auto",
            },
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        if forecast.status_code >= 400:
            return _error(started, "http_error", f"Forecast HTTP {forecast.status_code}", city=city, source="open-meteo")
        data = forecast.json()
        current = data.get("current") or {}
    except httpx.TimeoutException:
        return _error(started, "timeout", "天气请求超时", city=city, source="open-meteo")
    except httpx.HTTPError as exc:
        return _error(started, "http_error", str(exc), city=city, source="open-meteo")
    except Exception as exc:
        return _error(started, "parse_error", f"{type(exc).__name__}: {exc}", city=city, source="open-meteo")

    return {
        "ok": True,
        "city": place.get("name", city),
        "country": place.get("country", ""),
        "latitude": place.get("latitude"),
        "longitude": place.get("longitude"),
        "temperature": current.get("temperature_2m"),
        "wind_speed": current.get("wind_speed_10m"),
        "weather_code": current.get("weather_code"),
        "timezone": data.get("timezone", ""),
        "source": "open-meteo",
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
        "error": None,
    }
