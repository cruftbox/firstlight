import responses as resp_lib
from unittest.mock import patch


API_URL = "https://api.example.com/tasks"

SAMPLE_ITEMS = [
    {"title": "Buy milk", "is_completed": False, "project_id": "inbox"},
    {"title": "Send report", "is_completed": False, "project_id": "work"},
    {"title": "Old task", "is_completed": True, "project_id": "inbox"},
]


@resp_lib.activate
def test_returns_incomplete_tasks():
    resp_lib.add(resp_lib.GET, API_URL, json=SAMPLE_ITEMS, status=200)
    from app.providers.tasks_api import get_tasks
    result = get_tasks(API_URL, api_key="token123")
    assert "Buy milk" in result
    assert "Send report" in result
    assert "Old task" not in result


@resp_lib.activate
def test_filter_restricts_by_project():
    resp_lib.add(resp_lib.GET, API_URL, json=SAMPLE_ITEMS, status=200)
    from app.providers.tasks_api import get_tasks
    result = get_tasks(API_URL, api_key="token123", api_filter="inbox")
    assert result == ["Buy milk"]


@resp_lib.activate
def test_filter_is_case_insensitive():
    resp_lib.add(resp_lib.GET, API_URL, json=SAMPLE_ITEMS, status=200)
    from app.providers.tasks_api import get_tasks
    result = get_tasks(API_URL, api_key="token123", api_filter="INBOX")
    assert result == ["Buy milk"]


@resp_lib.activate
def test_returns_empty_on_http_error():
    resp_lib.add(resp_lib.GET, API_URL, status=401)
    from app.providers.tasks_api import get_tasks
    result = get_tasks(API_URL, api_key="badtoken")
    assert result == []


@resp_lib.activate
def test_returns_empty_on_network_error():
    resp_lib.add(resp_lib.GET, API_URL, body=ConnectionError("network"))
    from app.providers.tasks_api import get_tasks
    result = get_tasks(API_URL, api_key="token123")
    assert result == []


def test_returns_empty_when_url_not_configured():
    from app.providers.tasks_api import get_tasks
    assert get_tasks("") == []


@resp_lib.activate
def test_sends_bearer_token_header():
    resp_lib.add(resp_lib.GET, API_URL, json=[], status=200)
    from app.providers.tasks_api import get_tasks
    get_tasks(API_URL, api_key="mytoken")
    assert resp_lib.calls[0].request.headers.get("Authorization") == "Bearer mytoken"
