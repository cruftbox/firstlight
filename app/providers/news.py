import feedparser
import hashlib
import logging
from datetime import datetime, timedelta, timezone


def get_news(feeds: list, max_age_hours: int = 24, max_items: int = 10) -> list:
    """Returns list of {"title", "url", "label"} deduped by title, within max_age_hours.

    Entries without a publication date are included unconditionally.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    seen: set = set()
    items: list = []

    for feed_cfg in feeds:
        url = feed_cfg.get("url", "")
        label = feed_cfg.get("label", "")
        try:
            feed = feedparser.parse(url)
        except Exception:
            continue
        if getattr(feed, "bozo", False) and not getattr(feed, "entries", []):
            logging.warning("Feed error for %s: %s", url, getattr(feed, "bozo_exception", "unknown"))
            continue

        for entry in feed.entries:
            title = getattr(entry, "title", "").strip()
            link = getattr(entry, "link", "")

            dedup_key = hashlib.md5(title.lower().encode()).hexdigest()
            if dedup_key in seen:
                continue

            published = getattr(entry, "published_parsed", None)
            if published:
                pub_dt = datetime(*published[:6], tzinfo=timezone.utc)
                if pub_dt < cutoff:
                    continue

            seen.add(dedup_key)
            items.append({"title": title, "url": link, "label": label})
            if len(items) >= max_items:
                return items

    return items
