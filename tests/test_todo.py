import json
from unittest.mock import patch, MagicMock
from app import create_app

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


def test_todo_api_get_returns_list():
    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as client:
        with patch("app.config.load", return_value=MINIMAL_CONFIG):
            with patch("app.routes.todo.TODOS_PATH") as mock_path:
                mock_path.exists.return_value = False
                resp = client.get("/api/todos")

    assert resp.status_code == 200
    assert resp.get_json() == []


def test_todo_api_post_creates_item():
    app = create_app()
    app.config["TESTING"] = True

    saved_todos = []

    def fake_save(todos):
        saved_todos.clear()
        saved_todos.extend(todos)

    with app.test_client() as client:
        with patch("app.config.load", return_value=MINIMAL_CONFIG):
            with patch("app.routes.todo.TODOS_PATH") as mock_path:
                mock_path.exists.return_value = False
                with patch("app.routes.todo._save", side_effect=fake_save):
                    resp = client.post(
                        "/api/todos",
                        data=json.dumps({"text": "Buy milk"}),
                        content_type="application/json",
                    )

    assert resp.status_code == 201
    data = resp.get_json()
    assert data["text"] == "Buy milk"
    assert data["done"] is False
    assert "id" in data


def test_todo_api_delete_removes_item():
    app = create_app()
    app.config["TESTING"] = True

    existing_todos = [{"id": "abc-123", "text": "Buy milk", "done": False}]

    with app.test_client() as client:
        with patch("app.config.load", return_value=MINIMAL_CONFIG):
            with patch("app.routes.todo._load", return_value=existing_todos):
                with patch("app.routes.todo._save") as mock_save:
                    resp = client.delete(
                        "/api/todos",
                        data=json.dumps({"id": "abc-123"}),
                        content_type="application/json",
                    )
                    saved_arg = mock_save.call_args[0][0]

    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}
    assert all(t["id"] != "abc-123" for t in saved_arg)


def test_todo_api_post_rejects_empty_text():
    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as client:
        with patch("app.config.load", return_value=MINIMAL_CONFIG):
            with patch("app.routes.todo.TODOS_PATH") as mock_path:
                mock_path.exists.return_value = False
                resp = client.post(
                    "/api/todos",
                    data=json.dumps({"text": "   "}),
                    content_type="application/json",
                )

    assert resp.status_code == 400
    assert "error" in resp.get_json()
