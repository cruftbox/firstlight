import logging
from pathlib import Path
import json


def collect_data(config: dict) -> dict:
    """Collect data from all providers. Each provider fails gracefully to empty/None."""
    from app.providers import weather, quote, news, sports, history
    from app.providers import calendar as cal_provider

    loc = config["location"]
    weather_data = None
    if loc.get("lat"):
        try:
            weather_data = weather.get_forecast(loc["lat"], loc["lon"], config["weather"]["units"])
        except Exception as e:
            logging.warning("Weather provider failed: %s", e)

    tz_str = config["firstlight"]["timezone"]
    quote_data = None
    if config["quote"]["enabled"]:
        try:
            quote_data = quote.get_quote(tz_str)
        except Exception as e:
            logging.warning("Quote provider failed: %s", e)

    calendar_data = []
    calendar_tomorrow = []
    if config["calendar"]["enabled"]:
        try:
            calendar_data = cal_provider.get_events(config["calendar"]["calendar_ids"], timezone_str=tz_str)
            calendar_tomorrow = cal_provider.get_events(config["calendar"]["calendar_ids"], day_offset=1, timezone_str=tz_str)
        except Exception as e:
            logging.warning("Calendar provider failed: %s", e)

    try:
        sports_data = sports.get_scores(config["sports"], config["firstlight"]["timezone"])
    except Exception as e:
        logging.warning("Sports provider failed: %s", e)
        sports_data = []

    try:
        news_data = news.get_news(
            config["news"]["feeds"],
            config["news"]["max_age_hours"],
            config["news"]["max_items"],
        )
    except Exception as e:
        logging.warning("News provider failed: %s", e)
        news_data = []

    history_data = []
    if config.get("history", {}).get("enabled", True):
        try:
            history_data = history.get_events(tz_str=tz_str)
        except Exception as e:
            logging.warning("History provider failed: %s", e)

    return {
        "weather": weather_data,
        "quote": quote_data,
        "calendar": calendar_data,
        "calendar_tomorrow": calendar_tomorrow,
        "sports": sports_data,
        "news": news_data,
        "todos": _load_todos(),
        "history": history_data,
    }


def _load_todos() -> list:
    todos_path = Path("/app/config/todos.json")
    if not todos_path.exists():
        return []
    try:
        items = json.loads(todos_path.read_text())
        return [item for item in items if not item.get("done", False)]
    except Exception:
        return []


def run_pipeline() -> bytes:
    """Collect → render → archive/print/email. Returns PDF bytes. All errors logged, not raised."""
    from datetime import date
    from app.config import load as load_config
    from app.print.renderer import render_digest

    config = load_config()
    today = date.today()
    data = collect_data(config)
    pdf_bytes = render_digest(data, config)

    if config["archive"]["enabled"]:
        try:
            from app.print.archive import save, cleanup
            save(pdf_bytes, today)
            cleanup(config["archive"]["retention_days"])
        except Exception as e:
            logging.error("Archive error: %s", e)

    if config["firstlight"]["printer"]:
        try:
            from app.print.printer import print_pdf
            print_pdf(
                pdf_bytes,
                config["firstlight"]["printer"],
                config["firstlight"].get("printer_ip", ""),
            )
        except Exception as e:
            logging.error("Printer error: %s", e)

    if config["email"]["enabled"]:
        try:
            from app.print.emailer import send
            send(pdf_bytes, today, config["email"])
        except Exception as e:
            logging.error("Email error: %s", e)

    return pdf_bytes
