from mini_agent.skills.builtin.weather import weather_open_meteo


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


def test_weather_open_meteo_success(monkeypatch):
    responses = [
        FakeResponse({"results": [{"name": "武汉", "country": "中国", "latitude": 30.58, "longitude": 114.27}]}),
        FakeResponse({"timezone": "Asia/Shanghai", "current": {"temperature_2m": 28, "wind_speed_10m": 5, "weather_code": 1}}),
    ]
    monkeypatch.setattr("mini_agent.skills.builtin.weather.httpx.get", lambda *args, **kwargs: responses.pop(0))

    result = weather_open_meteo("武汉")

    assert result["ok"] is True
    assert result["temperature"] == 28
    assert result["source"] == "open-meteo"


def test_weather_city_not_found(monkeypatch):
    monkeypatch.setattr("mini_agent.skills.builtin.weather.httpx.get", lambda *args, **kwargs: FakeResponse({"results": []}))

    result = weather_open_meteo("不存在城市")

    assert result["ok"] is False
    assert result["error"]["code"] == "city_not_found"


def test_weather_http_error(monkeypatch):
    monkeypatch.setattr("mini_agent.skills.builtin.weather.httpx.get", lambda *args, **kwargs: FakeResponse({}, status_code=500))

    result = weather_open_meteo("武汉")

    assert result["ok"] is False
    assert result["error"]["code"] == "http_error"
