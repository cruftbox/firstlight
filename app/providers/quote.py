import logging
import requests
from datetime import datetime
from threading import Lock
import pytz

_cache: dict = {"date": None, "data": None}
_cache_lock = Lock()


def get_quote(tz_str: str = "UTC") -> dict | None:
    """Returns {"text": str, "author": str} or None on failure. Cached daily."""
    try:
        tz = pytz.timezone(tz_str)
    except Exception:
        tz = pytz.utc
    today = datetime.now(tz).date().isoformat()
    with _cache_lock:
        if _cache["date"] == today:
            return _cache["data"]

    try:
        resp = requests.get("https://zenquotes.io/api/today", timeout=10)
        resp.raise_for_status()
        items = resp.json()
        if not items:
            logging.warning("Quote provider: empty response from zenquotes.io")
            return None
        item = items[0]
        result = {"text": item["q"], "author": item["a"]}
    except Exception as e:
        logging.warning("Quote provider failed: %s", e)
        return None

    with _cache_lock:
        _cache["date"] = today
        _cache["data"] = result

    return result
