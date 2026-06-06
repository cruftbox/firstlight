import logging
import time
import requests


def get_with_retry(url: str, *, attempts: int = 3, delay: float = 3.0, **kwargs) -> requests.Response:
    """GET a URL with up to `attempts` tries, sleeping `delay` seconds between them.

    Raises the last exception if all attempts fail.
    """
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            resp = requests.get(url, **kwargs)
            resp.raise_for_status()
            return resp
        except Exception as e:
            last_exc = e
            if attempt < attempts:
                logging.debug("Attempt %d/%d failed for %s: %s — retrying in %.0fs", attempt, attempts, url, e, delay)
                time.sleep(delay)
    raise last_exc
