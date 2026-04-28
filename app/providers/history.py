import random
import requests
from datetime import date


def get_events(count: int = 2) -> list:
    """Return list of {"year", "text"} from Wikipedia's On This Day API."""
    today = date.today()
    url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{today.month}/{today.day}"
    try:
        resp = requests.get(url, headers={"User-Agent": "firstlight-digest/1.0"}, timeout=10)
        resp.raise_for_status()
        events = resp.json().get("events", [])
    except Exception:
        return []

    # Filter out very recent events (last 5 years) for more interesting history
    cutoff = today.year - 5
    filtered = [e for e in events if e.get("year", 9999) <= cutoff]
    if not filtered:
        filtered = events

    # Use date ordinal as seed so results are consistent within the same day
    rng = random.Random(today.toordinal())
    sample = rng.sample(filtered, min(count, len(filtered)))
    sample.sort(key=lambda e: e.get("year", 0))

    return [{"year": e["year"], "text": e["text"]} for e in sample]
