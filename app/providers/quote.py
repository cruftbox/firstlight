import requests
from datetime import date
from threading import Lock

_cache: dict = {"date": None, "data": None}
_cache_lock = Lock()


def get_quote() -> dict | None:
    """Returns {"text": str, "author": str} or None on failure. Cached daily."""
    today = date.today().isoformat()
    with _cache_lock:
        if _cache["date"] == today:
            return _cache["data"]

    try:
        resp = requests.get("https://zenquotes.io/api/today", timeout=10)
        resp.raise_for_status()
        items = resp.json()
        if not items:
            return None
        item = items[0]
        result = {"text": item["q"], "author": item["a"]}
    except Exception:
        return None

    with _cache_lock:
        _cache["date"] = today
        _cache["data"] = result

    return result
