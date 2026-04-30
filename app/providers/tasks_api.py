"""
Template API provider for fetching to-do items from an external service.

To adapt this for a specific service:
  1. Update _fetch_items() to match the service's authentication scheme and
     endpoint structure.
  2. Update _extract_text() to pull the task text from one item in the
     response payload.
  3. Update _matches_filter() to apply whatever label/project/tag filtering
     the service supports. Delete it if filtering is not needed.

Configuration (set in Settings → To-Do or config/firstlight.yaml):
  tasks.api_url    — full endpoint URL, e.g. https://api.example.com/tasks
  tasks.api_key    — bearer token or API key
  tasks.api_filter — optional label/project/tag name to restrict results
                     (leave blank to include all incomplete tasks)
"""

import logging
import requests


def get_tasks(api_url: str, api_key: str = "", api_filter: str = "") -> list:
    if not api_url:
        logging.warning("tasks_api: api_url is not configured")
        return []

    try:
        items = _fetch_items(api_url, api_key)
    except Exception as e:
        logging.warning("tasks_api: request failed: %s", e)
        return []

    tasks = []
    for item in items:
        if _is_complete(item):
            continue
        if api_filter and not _matches_filter(item, api_filter):
            continue
        text = _extract_text(item)
        if text:
            tasks.append(text)
    return tasks


# ── Customise the three functions below for your service ─────────────────────

def _fetch_items(api_url: str, api_key: str) -> list:
    """Make the API request and return the raw list of task objects.

    Most REST APIs accept a bearer token in the Authorization header.
    Some use a custom header (e.g. X-API-Key) or query-string parameters.
    Adjust headers and params to match your service's documentation.

    Expected return: a list of dicts, one per task.

    Example services:
      Todoist  — GET https://api.todoist.com/rest/v2/tasks
                 header: Authorization: Bearer <api_key>
      TickTick — GET https://api.ticktick.com/open/v1/project/.../tasks
                 header: Authorization: Bearer <api_key>
      Vikunja  — GET https://<host>/api/v1/tasks/all
                 header: Authorization: Bearer <api_key>
    """
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    response = requests.get(api_url, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()
    # If the API wraps items in a key, unwrap it here, e.g.:
    #   return data["items"]
    #   return data["tasks"]
    # If the response is a bare list, return it directly:
    return data if isinstance(data, list) else []


def _extract_text(item: dict) -> str:
    """Return the display text for one task item.

    Common field names across services:
      "content"  — Todoist
      "title"    — TickTick, Vikunja, most others
      "name"     — some services
    """
    return (item.get("content") or item.get("title") or item.get("name") or "").strip()


def _is_complete(item: dict) -> bool:
    """Return True if the task is already done and should be skipped.

    Common patterns:
      item.get("is_completed")          — Todoist (bool)
      item.get("status") == 2           — TickTick (int, 0=active 2=done)
      item.get("done")                  — Vikunja, generic (bool)
      item.get("completed_at") is not None  — timestamp-based
    """
    return bool(item.get("is_completed") or item.get("done"))


def _matches_filter(item: dict, filter_value: str) -> bool:
    """Return True if this task belongs to the configured project/label/tag.

    api_filter is compared case-insensitively against whatever grouping field
    your service uses. Common patterns:

      Todoist  — item["project_id"] == filter_value
                 or any(l["name"] for l in item.get("labels", []))
      TickTick — item.get("projectId") == filter_value
      Vikunja  — item.get("project", {}).get("title", "").lower()
    """
    project = (item.get("project") or {})
    candidates = [
        str(item.get("project_id", "")),
        str(item.get("projectId", "")),
        project.get("title", "") if isinstance(project, dict) else "",
        item.get("list", ""),
    ]
    needle = filter_value.lower()
    return any(c.lower() == needle for c in candidates if c)
