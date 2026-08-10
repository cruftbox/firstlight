import pytest
import responses as resp_lib
from unittest.mock import patch as _patch
from datetime import datetime, timezone, timedelta

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


def test_get_news_dedup_does_not_suppress_fresh_entry_when_stale_seen_first():
    stale = _make_entry("Breaking News", "https://a.com/1", hours_ago=30)
    fresh = _make_entry("Breaking News", "https://b.com/1", hours_ago=1)
    fake_a = _fake_feed([stale])
    fake_b = _fake_feed([fresh])

    call_count = [0]
    def fake_parse(url):
        call_count[0] += 1
        return fake_a if call_count[0] == 1 else fake_b

    with _patch("feedparser.parse", side_effect=fake_parse):
        from app.providers.news import get_news
        items = get_news(
            [{"url": "https://a.com/rss", "label": "A"},
             {"url": "https://b.com/rss", "label": "B"}],
            max_age_hours=24, max_items=10,
        )
    assert len(items) == 1
    assert items[0]["label"] == "B"

# ── Sports ────────────────────────────────────────────────────────────────────

MLB_URL = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"

MLB_FINAL = {
    "events": [{
        "name": "Dodgers at Giants",
        "date": "2026-04-28T02:10Z",
        "status": {"type": {"name": "STATUS_FINAL", "completed": True}},
        "competitions": [{
            "competitors": [
                {"team": {"id": "19", "name": "Dodgers", "abbreviation": "LAD"}, "score": "4", "homeAway": "home"},
                {"team": {"id": "26", "name": "Giants", "abbreviation": "SF"}, "score": "2", "homeAway": "away"},
            ]
        }]
    }]
}

MLB_UPCOMING = {
    "events": [{
        "name": "Dodgers at Giants",
        "date": "2026-04-28T20:10Z",
        "status": {"type": {"name": "STATUS_SCHEDULED", "completed": False}},
        "competitions": [{
            "competitors": [
                {"team": {"id": "19", "name": "Dodgers", "abbreviation": "LAD"}, "score": "0", "homeAway": "home"},
                {"team": {"id": "26", "name": "Giants", "abbreviation": "SF"}, "score": "0", "homeAway": "away"},
            ]
        }]
    }]
}

MLB_NONE = {"events": []}

MLB_TEAMS_URL = MLB_URL.replace("/scoreboard", "/teams")

MLB_ROSTER = {
    "sports": [{"leagues": [{"teams": [
        {"team": {"id": "19", "abbreviation": "LAD", "name": "Dodgers",
                  "displayName": "Los Angeles Dodgers"}},
        {"team": {"id": "26", "abbreviation": "SF", "name": "Giants",
                  "displayName": "San Francisco Giants"}},
    ]}]}]
}

EMPTY_SPORTS = {"mlb": [], "nfl": [], "nba": [], "wnba": [], "mls": [], "premier_league": []}


@resp_lib.activate
def test_sports_final_game():
    # get_scores fetches yesterday then today; register both so one game is
    # not counted twice.
    resp_lib.add(resp_lib.GET, MLB_TEAMS_URL, json=MLB_ROSTER, status=200)
    resp_lib.add(resp_lib.GET, MLB_URL, json=MLB_FINAL, status=200)
    resp_lib.add(resp_lib.GET, MLB_URL, json=MLB_NONE, status=200)
    from app.providers.sports import get_scores
    results = get_scores({**EMPTY_SPORTS, "mlb": ["LAD"]})
    assert len(results) == 1
    assert "Final" in results[0]["text"]
    assert "Dodgers" in results[0]["text"]
    assert results[0]["emoji"] == "⚾"


@resp_lib.activate
def test_sports_upcoming_game():
    resp_lib.add(resp_lib.GET, MLB_TEAMS_URL, json=MLB_ROSTER, status=200)
    resp_lib.add(resp_lib.GET, MLB_URL, json=MLB_NONE, status=200)
    resp_lib.add(resp_lib.GET, MLB_URL, json=MLB_UPCOMING, status=200)
    from app.providers.sports import get_scores
    results = get_scores({**EMPTY_SPORTS, "mlb": ["LAD"]})
    assert len(results) == 1
    assert "Dodgers" in results[0]["text"]
    assert "Final" not in results[0]["text"]


# ── Unknown-team warnings ─────────────────────────────────────────────────────


@resp_lib.activate
def test_sports_warns_on_unrecognized_team():
    """A stale abbreviation (the real ACFC/LAK bug) must not fail silently."""
    resp_lib.add(resp_lib.GET, MLB_TEAMS_URL, json=MLB_ROSTER, status=200)
    resp_lib.add(resp_lib.GET, MLB_URL, json=MLB_NONE, status=200)
    resp_lib.add(resp_lib.GET, MLB_URL, json=MLB_NONE, status=200)
    from app.providers.sports import get_scores
    warnings = []
    get_scores({**EMPTY_SPORTS, "mlb": ["NOPE"]}, warnings=warnings)
    assert len(warnings) == 1
    assert "NOPE" in warnings[0]
    assert "MLB" in warnings[0]


@resp_lib.activate
def test_sports_no_warning_for_valid_abbreviation():
    resp_lib.add(resp_lib.GET, MLB_TEAMS_URL, json=MLB_ROSTER, status=200)
    resp_lib.add(resp_lib.GET, MLB_URL, json=MLB_NONE, status=200)
    resp_lib.add(resp_lib.GET, MLB_URL, json=MLB_NONE, status=200)
    from app.providers.sports import get_scores
    warnings = []
    get_scores({**EMPTY_SPORTS, "mlb": ["LAD"]}, warnings=warnings)
    assert warnings == []


@resp_lib.activate
def test_sports_no_warning_for_valid_team_name():
    """_format_event matches on name as well as abbreviation; so must the check."""
    resp_lib.add(resp_lib.GET, MLB_TEAMS_URL, json=MLB_ROSTER, status=200)
    resp_lib.add(resp_lib.GET, MLB_URL, json=MLB_NONE, status=200)
    resp_lib.add(resp_lib.GET, MLB_URL, json=MLB_NONE, status=200)
    from app.providers.sports import get_scores
    warnings = []
    get_scores({**EMPTY_SPORTS, "mlb": ["Dodgers"]}, warnings=warnings)
    assert warnings == []


@resp_lib.activate
def test_sports_no_warning_when_roster_unavailable():
    """Fail open — an unreachable roster must not accuse a valid team."""
    resp_lib.add(resp_lib.GET, MLB_TEAMS_URL, status=500)
    resp_lib.add(resp_lib.GET, MLB_URL, json=MLB_NONE, status=200)
    resp_lib.add(resp_lib.GET, MLB_URL, json=MLB_NONE, status=200)
    from app.providers.sports import get_scores
    warnings = []
    get_scores({**EMPTY_SPORTS, "mlb": ["LAD"]}, warnings=warnings)
    assert warnings == []


@resp_lib.activate
@pytest.mark.parametrize("configured", ["LAD", "Dodgers", "Los Angeles Dodgers", "19", "  lad  "])
def test_sports_resolves_any_label_to_the_same_team(configured):
    """Abbreviation, name, display name or raw id must all find the Dodgers."""
    resp_lib.add(resp_lib.GET, MLB_TEAMS_URL, json=MLB_ROSTER, status=200)
    resp_lib.add(resp_lib.GET, MLB_URL, json=MLB_FINAL, status=200)
    resp_lib.add(resp_lib.GET, MLB_URL, json=MLB_NONE, status=200)
    from app.providers.sports import get_scores
    warnings = []
    results = get_scores({**EMPTY_SPORTS, "mlb": [configured]}, warnings=warnings)
    assert len(results) == 1
    assert "Dodgers" in results[0]["text"]
    assert warnings == []


@resp_lib.activate
def test_sports_matches_by_id_when_abbreviation_has_changed():
    """The Angel City case: config holds a label ESPN has since retired.

    The roster still maps the old *name* to the id, so the game is found even
    though the abbreviation in the event payload no longer matches the config.
    """
    roster = {"sports": [{"leagues": [{"teams": [
        {"team": {"id": "19", "abbreviation": "NEWABBR", "name": "Dodgers"}},
        {"team": {"id": "26", "abbreviation": "SF", "name": "Giants"}},
    ]}]}]}
    resp_lib.add(resp_lib.GET, MLB_TEAMS_URL, json=roster, status=200)
    resp_lib.add(resp_lib.GET, MLB_URL, json=MLB_FINAL, status=200)
    resp_lib.add(resp_lib.GET, MLB_URL, json=MLB_NONE, status=200)
    from app.providers.sports import get_scores
    warnings = []
    results = get_scores({**EMPTY_SPORTS, "mlb": ["Dodgers"]}, warnings=warnings)
    assert len(results) == 1
    assert warnings == []


@resp_lib.activate
def test_sports_falls_back_to_labels_when_roster_unavailable():
    """A roster outage must degrade accuracy, not empty the digest."""
    resp_lib.add(resp_lib.GET, MLB_TEAMS_URL, status=500)
    resp_lib.add(resp_lib.GET, MLB_URL, json=MLB_FINAL, status=200)
    resp_lib.add(resp_lib.GET, MLB_URL, json=MLB_NONE, status=200)
    from app.providers.sports import get_scores
    warnings = []
    results = get_scores({**EMPTY_SPORTS, "mlb": ["LAD"]}, warnings=warnings)
    assert len(results) == 1
    assert warnings == []  # unverifiable is not the same as wrong


@resp_lib.activate
def test_sports_ambiguous_label_is_not_guessed():
    """A label naming two teams resolves to neither, rather than to the wrong one."""
    roster = {"sports": [{"leagues": [{"teams": [
        {"team": {"id": "19", "abbreviation": "LAD", "name": "Kings"}},
        {"team": {"id": "26", "abbreviation": "SF", "name": "Kings"}},
    ]}]}]}
    resp_lib.add(resp_lib.GET, MLB_TEAMS_URL, json=roster, status=200)
    resp_lib.add(resp_lib.GET, MLB_URL, json=MLB_NONE, status=200)
    resp_lib.add(resp_lib.GET, MLB_URL, json=MLB_NONE, status=200)
    from app.providers.sports import get_scores
    warnings = []
    get_scores({**EMPTY_SPORTS, "mlb": ["Kings"]}, warnings=warnings)
    assert len(warnings) == 1
    assert "Kings" in warnings[0]


@resp_lib.activate
def test_sports_scores_still_returned_when_team_unrecognized():
    """A warning must not suppress the rest of the league's output."""
    resp_lib.add(resp_lib.GET, MLB_TEAMS_URL, json=MLB_ROSTER, status=200)
    resp_lib.add(resp_lib.GET, MLB_URL, json=MLB_FINAL, status=200)
    resp_lib.add(resp_lib.GET, MLB_URL, json=MLB_NONE, status=200)
    from app.providers.sports import get_scores
    warnings = []
    results = get_scores({**EMPTY_SPORTS, "mlb": ["LAD", "NOPE"]}, warnings=warnings)
    assert len(results) == 1
    assert len(warnings) == 1


@resp_lib.activate
def test_sports_no_matching_team():
    resp_lib.add(resp_lib.GET, MLB_TEAMS_URL, json=MLB_ROSTER, status=200)
    resp_lib.add(resp_lib.GET, MLB_URL, json=MLB_FINAL, status=200)
    resp_lib.add(resp_lib.GET, MLB_URL, json=MLB_NONE, status=200)
    from app.providers.sports import get_scores
    results = get_scores({**EMPTY_SPORTS, "mlb": ["Yankees"]})
    assert results == []


def test_sports_empty_config():
    from app.providers.sports import get_scores
    results = get_scores(EMPTY_SPORTS)
    assert results == []  # no HTTP made — nothing to request


@resp_lib.activate
def test_sports_network_error():
    resp_lib.add(resp_lib.GET, MLB_TEAMS_URL, json=MLB_ROSTER, status=200)
    resp_lib.add(resp_lib.GET, MLB_URL, body=ConnectionError("network"))
    from app.providers.sports import get_scores
    results = get_scores({**EMPTY_SPORTS, "mlb": ["LAD"]})
    assert results == []

# ── Calendar ──────────────────────────────────────────────────────────────────


def test_calendar_returns_empty_when_no_token(tmp_path):
    import app.providers.calendar as cal_mod
    with _patch("app.providers.calendar.TOKEN_PATH", tmp_path / "missing_token.json"):
        events = cal_mod.get_events(["primary"])
    assert events == []


def test_calendar_returns_empty_on_invalid_token(tmp_path):
    token_file = tmp_path / "token.json"
    token_file.write_text('{"invalid": true, "no_fields": "here"}', encoding="utf-8")
    import app.providers.calendar as cal_mod
    with _patch("app.providers.calendar.TOKEN_PATH", token_file):
        events = cal_mod.get_events(["primary"])
    assert events == []


def test_calendar_returns_events_with_valid_credentials(tmp_path):
    from unittest.mock import MagicMock
    mock_creds = MagicMock()
    mock_creds.valid = True
    mock_creds.expired = False

    mock_event_list = {
        "items": [
            {
                "summary": "Team standup",
                "start": {"dateTime": "2026-04-28T09:00:00-07:00"},
            },
            {
                "summary": "Company holiday",
                "start": {"date": "2026-04-28"},
            },
        ]
    }
    mock_service = MagicMock()
    mock_service.events.return_value.list.return_value.execute.return_value = mock_event_list

    import app.providers.calendar as cal_mod
    with _patch("app.providers.calendar._get_credentials", return_value=mock_creds), \
         _patch("googleapiclient.discovery.build", return_value=mock_service):
        events = cal_mod.get_events(["primary"])

    assert len(events) == 2
    assert events[0]["title"] == "Company holiday"
    assert events[0]["all_day"] is True
    
    assert events[1]["title"] == "Team standup"
    assert events[1]["all_day"] is False
    assert isinstance(events[1]["time"], str)
