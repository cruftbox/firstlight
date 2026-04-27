import pytest


MINIMAL_CONFIG = {
    "firstlight": {
        "paper_size": "letter",
        "timezone": "America/Los_Angeles",
        "printer": "",
        "print_time": "06:30",
        "setup_complete": True,
    },
    "location": {"city": "Portland", "lat": 45.52, "lon": -122.68},
    "weather": {"units": "imperial"},
    "quote": {"enabled": True},
    "archive": {"enabled": False, "retention_days": 30},
    "email": {
        "enabled": False, "smtp_host": "", "smtp_port": 587,
        "smtp_user": "", "smtp_password": "", "from_address": "", "to_address": "",
    },
    "calendar": {"enabled": False, "google_credentials": "", "calendar_ids": ["primary"]},
    "sports": {"mlb": [], "nfl": [], "nba": [], "wnba": [], "mls": [], "premier_league": []},
    "news": {"max_age_hours": 24, "max_items": 10, "feeds": []},
}

MINIMAL_DATA = {
    "weather": {
        "condition": "Clear sky", "temp": 68, "high": 75, "low": 50,
        "units": "imperial", "hourly": [{"hour": 6, "temp": 55}],
    },
    "quote": {"text": "Test quote.", "author": "Tester"},
    "calendar": [],
    "sports": [],
    "news": [],
    "todos": [],
}


def test_render_returns_pdf_bytes():
    from app.print.renderer import render_digest
    pdf = render_digest(MINIMAL_DATA, MINIMAL_CONFIG)
    assert isinstance(pdf, bytes)
    assert pdf[:4] == b"%PDF"


def test_render_with_no_quote():
    from app.print.renderer import render_digest
    data = {**MINIMAL_DATA, "quote": None}
    pdf = render_digest(data, MINIMAL_CONFIG)
    assert pdf[:4] == b"%PDF"


def test_render_with_all_sections():
    from app.print.renderer import render_digest
    data = {
        **MINIMAL_DATA,
        "sports": [{"emoji": "⚾", "text": "Dodgers 4, Giants 2  Final"}],
        "news": [{"title": "Big news today", "url": "https://example.com", "label": "Tech"}],
        "todos": [{"text": "Buy milk", "done": False}],
        "calendar": [{"time": "9:00 AM", "title": "Standup", "all_day": False}],
    }
    pdf = render_digest(data, MINIMAL_CONFIG)
    assert pdf[:4] == b"%PDF"
