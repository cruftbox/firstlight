import feedparser
import hashlib
import html
import logging
from datetime import datetime, timedelta, timezone

_EPOCH = datetime.min.replace(tzinfo=timezone.utc)


def get_news(feeds: list, max_age_hours: int = 24, max_items: int = 10) -> list:
    """Returns list of {"title", "url", "label"} using round-robin across feeds.

    Each feed contributes items in recency order; items are then interleaved
    one-per-feed per round so no single feed dominates the results.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    seen: set = set()
    buckets: list = []

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

        feed_items = []
        for entry in feed.entries:
            title = html.unescape(getattr(entry, "title", "").strip())
            link = getattr(entry, "link", "")

            dedup_key = hashlib.md5(title.lower().encode()).hexdigest()
            if dedup_key in seen:
                continue

            pub_dt = None
            published = getattr(entry, "published_parsed", None)
            if published:
                pub_dt = datetime(*published[:6], tzinfo=timezone.utc)
                if pub_dt < cutoff:
                    continue

            seen.add(dedup_key)
            feed_items.append({"title": title, "url": link, "label": label, "_pub_dt": pub_dt or _EPOCH})

        if feed_items:
            feed_items.sort(key=lambda x: x["_pub_dt"], reverse=True)
            buckets.append(feed_items)

    result = []
    i = 0
    while len(result) < max_items:
        added = False
        for bucket in buckets:
            if i < len(bucket) and len(result) < max_items:
                item = bucket[i]
                result.append({"title": item["title"], "url": item["url"], "label": item["label"]})
                added = True
        if not added:
            break
        i += 1

    return result
