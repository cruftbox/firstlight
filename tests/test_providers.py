import pytest
import responses as resp_lib

# ── Weather ───────────────────────────────────────────────────────────────────

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

GEOCODE_RESPONSE = {
    "results": [{"name": "Portland", "latitude": 45.52, "longitude": -122.68,
                 "country": "United States"}]
}

FORECAST_RESPONSE = {
    "current": {"temperature_2m": 68.0, "weathercode": 1, "windspeed_10m": 5.0},
    "hourly": {
        "time": [
            "2026-04-28T00:00", "2026-04-28T01:00", "2026-04-28T02:00",
            "2026-04-28T03:00", "2026-04-28T04:00", "2026-04-28T05:00",
            "2026-04-28T06:00", "2026-04-28T07:00", "2026-04-28T08:00",
            "2026-04-28T09:00", "2026-04-28T10:00", "2026-04-28T11:00",
            "2026-04-28T12:00", "2026-04-28T13:00", "2026-04-28T14:00",
            "2026-04-28T15:00", "2026-04-28T16:00", "2026-04-28T17:00",
            "2026-04-28T18:00", "2026-04-28T19:00", "2026-04-28T20:00",
            "2026-04-28T21:00", "2026-04-28T22:00", "2026-04-28T23:00",
        ],
        "temperature_2m": [
            55.0, 54.0, 53.0, 52.0, 51.0, 50.0,
            61.0, 63.0, 65.0, 67.0, 70.0, 72.0,
            74.0, 76.0, 77.0, 77.0, 76.0, 74.0,
            70.0, 68.0, 65.0, 63.0, 61.0, 59.0,
        ],
    },
    "daily": {"temperature_2m_max": [78.0], "temperature_2m_min": [50.0]},
}


@resp_lib.activate
def test_geocode_found():
    resp_lib.add(resp_lib.GET, GEOCODE_URL, json=GEOCODE_RESPONSE, status=200)
    from app.providers.weather import geocode
    result = geocode("Portland")
    assert result is not None
    assert result["name"] == "Portland"
    assert result["lat"] == 45.52
    assert result["lon"] == -122.68
    assert "country" in result


@resp_lib.activate
def test_geocode_not_found():
    resp_lib.add(resp_lib.GET, GEOCODE_URL, json={"results": []}, status=200)
    from app.providers.weather import geocode
    assert geocode("zzznonsense") is None


@resp_lib.activate
def test_geocode_returns_none_on_error():
    resp_lib.add(resp_lib.GET, GEOCODE_URL, body=ConnectionError("network error"))
    from app.providers.weather import geocode
    assert geocode("Portland") is None


@resp_lib.activate
def test_get_forecast_returns_expected_keys():
    from app.providers import weather as w
    w._cache.clear()
    resp_lib.add(resp_lib.GET, FORECAST_URL, json=FORECAST_RESPONSE, status=200)
    result = w.get_forecast(45.52, -122.68, "imperial")
    assert result is not None
    assert result["condition"] == "Mainly clear"
    assert result["temp"] == 68
    assert result["high"] == 78
    assert result["low"] == 50
    assert result["units"] == "imperial"
    assert "wind" in result
    assert result["wind"] == 5
    assert isinstance(result["hourly"], list)
    assert len(result["hourly"]) == 5  # 6am, 9am, 12pm, 3pm, 6pm


@resp_lib.activate
def test_get_forecast_uses_cache():
    from app.providers import weather as w
    w._cache.clear()
    resp_lib.add(resp_lib.GET, FORECAST_URL, json=FORECAST_RESPONSE, status=200)
    w.get_forecast(45.52, -122.68, "imperial")
    resp_lib.reset()  # remove mock — any HTTP would raise ConnectionError
    result = w.get_forecast(45.52, -122.68, "imperial")
    assert result is not None


@resp_lib.activate
def test_get_forecast_returns_none_on_error():
    from app.providers import weather as w
    w._cache.clear()
    resp_lib.add(resp_lib.GET, FORECAST_URL, body=ConnectionError("network error"))
    result = w.get_forecast(45.52, -122.68, "imperial")
    assert result is None

# ── Quote ─────────────────────────────────────────────────────────────────────

QUOTE_URL = "https://zenquotes.io/api/today"
QUOTE_RESPONSE = [{"q": "The secret of getting ahead is getting started.", "a": "Mark Twain", "h": ""}]


@resp_lib.activate
def test_get_quote_returns_text_and_author():
    from app.providers import quote as q
    q._cache["date"] = None
    resp_lib.add(resp_lib.GET, QUOTE_URL, json=QUOTE_RESPONSE, status=200)
    result = q.get_quote()
    assert result is not None
    assert result["text"] == "The secret of getting ahead is getting started."
    assert result["author"] == "Mark Twain"


@resp_lib.activate
def test_get_quote_uses_daily_cache():
    from app.providers import quote as q
    from datetime import date
    q._cache["date"] = date.today().isoformat()
    q._cache["data"] = {"text": "cached quote", "author": "Cache Author"}
    # No mock registered — any HTTP would raise ConnectionError
    result = q.get_quote()
    assert result["text"] == "cached quote"


@resp_lib.activate
def test_get_quote_returns_none_on_error():
    from app.providers import quote as q
    q._cache["date"] = None
    resp_lib.add(resp_lib.GET, QUOTE_URL, body=ConnectionError("network"))
    assert q.get_quote() is None

# ── News ──────────────────────────────────────────────────────────────────────

from unittest.mock import patch as _patch
from datetime import datetime, timezone, timedelta


def _make_entry(title, link, hours_ago=1):
    pub = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    return {"title": title, "link": link, "published_parsed": pub.timetuple()}


def _fake_feed(entries_dicts):
    entries = [type("E", (), d)() for d in entries_dicts]
    return type("Feed", (), {"entries": entries})()


def test_get_news_returns_items():
    fake = _fake_feed([
        _make_entry("AI chip rules", "https://example.com/1"),
        _make_entry("City transit plan", "https://example.com/2"),
    ])
    with _patch("feedparser.parse", return_value=fake):
        from app.providers.news import get_news
        items = get_news([{"url": "https://example.com/rss", "label": "Tech"}],
                         max_age_hours=24, max_items=10)
    assert len(items) == 2
    assert items[0]["title"] == "AI chip rules"
    assert items[0]["label"] == "Tech"


def test_get_news_filters_old_items():
    fake = _fake_feed([
        _make_entry("Recent", "https://example.com/1", hours_ago=1),
        _make_entry("Old", "https://example.com/2", hours_ago=30),
    ])
    with _patch("feedparser.parse", return_value=fake):
        from app.providers.news import get_news
        items = get_news([{"url": "https://example.com/rss", "label": "Tech"}],
                         max_age_hours=24, max_items=10)
    assert len(items) == 1
    assert items[0]["title"] == "Recent"


def test_get_news_deduplicates():
    entry_dict = _make_entry("Same headline", "https://example.com/1")
    fake = _fake_feed([entry_dict])
    with _patch("feedparser.parse", return_value=fake):
        from app.providers.news import get_news
        items = get_news(
            [{"url": "https://a.com/rss", "label": "A"},
             {"url": "https://b.com/rss", "label": "B"}],
            max_age_hours=24, max_items=10,
        )
    assert len(items) == 1


def test_get_news_respects_max_items():
    fake = _fake_feed([_make_entry(f"Item {i}", f"https://example.com/{i}") for i in range(20)])
    with _patch("feedparser.parse", return_value=fake):
        from app.providers.news import get_news
        items = get_news([{"url": "https://example.com/rss", "label": "Tech"}],
                         max_age_hours=24, max_items=5)
    assert len(items) == 5


def test_get_news_handles_bad_feed():
    with _patch("feedparser.parse", side_effect=Exception("network error")):
        from app.providers.news import get_news
        items = get_news([{"url": "https://broken.example/rss", "label": "Bad"}],
                         max_age_hours=24, max_items=10)
    assert items == []
