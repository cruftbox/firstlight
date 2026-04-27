import pytest
from datetime import date, timedelta
from unittest.mock import patch as _arch_patch, patch as _email_patch, MagicMock


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


def test_preview_route_returns_pdf():
    from unittest.mock import patch
    from app import create_app

    fake_pdf = b"%PDF-1.4 fake"
    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as client:
        with patch("app.config.load", return_value=MINIMAL_CONFIG):
            with patch("app.print.pipeline.collect_data", return_value=MINIMAL_DATA):
                with patch("app.print.renderer.render_digest", return_value=fake_pdf):
                    resp = client.get("/preview")

    assert resp.status_code == 200
    assert resp.content_type == "application/pdf"
    assert resp.data[:4] == b"%PDF"


# ── Archive ───────────────────────────────────────────────────────────────────


def test_archive_save_creates_file(tmp_path):
    import app.print.archive as arch
    with _arch_patch.object(arch, "ARCHIVE_DIR", tmp_path):
        arch.save(b"%PDF-test", date(2026, 4, 28))
    assert (tmp_path / "2026-04-28.pdf").exists()
    assert (tmp_path / "2026-04-28.pdf").read_bytes() == b"%PDF-test"


def test_archive_cleanup_removes_old(tmp_path):
    (tmp_path / "2026-01-01.pdf").write_bytes(b"old")
    (tmp_path / "2026-04-28.pdf").write_bytes(b"new")
    import app.print.archive as arch
    with _arch_patch.object(arch, "ARCHIVE_DIR", tmp_path):
        arch.cleanup(retention_days=30)
    assert not (tmp_path / "2026-01-01.pdf").exists()
    assert (tmp_path / "2026-04-28.pdf").exists()


def test_archive_list_all_sorted_newest_first(tmp_path):
    (tmp_path / "2026-04-26.pdf").write_bytes(b"a")
    (tmp_path / "2026-04-28.pdf").write_bytes(b"b")
    (tmp_path / "2026-04-27.pdf").write_bytes(b"c")
    import app.print.archive as arch
    with _arch_patch.object(arch, "ARCHIVE_DIR", tmp_path):
        files = arch.list_all()
    assert files[0]["filename"] == "2026-04-28.pdf"
    assert files[1]["filename"] == "2026-04-27.pdf"
    assert files[2]["filename"] == "2026-04-26.pdf"
    assert "size_kb" in files[0]
    assert "date" in files[0]


def test_archive_list_all_empty_when_no_dir(tmp_path):
    missing = tmp_path / "no_such_dir"
    import app.print.archive as arch
    with _arch_patch.object(arch, "ARCHIVE_DIR", missing):
        files = arch.list_all()
    assert files == []


# ── Emailer ───────────────────────────────────────────────────────────────────


def _make_email_config(port=587, user="user@example.com"):
    return {
        "smtp_host": "smtp.example.com",
        "smtp_port": port,
        "smtp_user": user,
        "smtp_password": "secret",
        "from_address": "from@example.com",
        "to_address": "to@example.com",
    }


def test_emailer_uses_starttls_for_port_587():
    mock_smtp = MagicMock()
    mock_instance = mock_smtp.return_value.__enter__.return_value
    with _email_patch("app.print.emailer.smtplib.SMTP", mock_smtp):
        from app.print.emailer import send
        result = send(b"%PDF", date(2026, 4, 28), _make_email_config(port=587))
    assert result is True
    mock_instance.starttls.assert_called_once()
    mock_instance.login.assert_called_once_with("user@example.com", "secret")


def test_emailer_uses_smtp_ssl_for_port_465():
    mock_ssl = MagicMock()
    mock_instance = mock_ssl.return_value.__enter__.return_value
    with _email_patch("app.print.emailer.smtplib.SMTP_SSL", mock_ssl):
        from app.print.emailer import send
        result = send(b"%PDF", date(2026, 4, 28), _make_email_config(port=465))
    assert result is True
    mock_instance.starttls.assert_not_called()


def test_emailer_skips_login_when_no_user():
    mock_smtp = MagicMock()
    mock_instance = mock_smtp.return_value.__enter__.return_value
    with _email_patch("app.print.emailer.smtplib.SMTP", mock_smtp):
        from app.print.emailer import send
        result = send(b"%PDF", date(2026, 4, 28), _make_email_config(user=""))
    assert result is True
    mock_instance.login.assert_not_called()


def test_emailer_returns_false_on_error():
    with _email_patch("app.print.emailer.smtplib.SMTP", side_effect=ConnectionRefusedError("refused")):
        from app.print.emailer import send
        result = send(b"%PDF", date(2026, 4, 28), _make_email_config())
    assert result is False
