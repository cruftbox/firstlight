import pytest
from unittest.mock import patch
from app import create_app


def test_create_app_registers_blueprints():
    app = create_app()
    blueprint_names = set(app.blueprints.keys())
    assert "setup" in blueprint_names
    assert "main" in blueprint_names
    assert "archive" in blueprint_names
    assert "todo" in blueprint_names


def test_root_redirects_to_setup_when_incomplete():
    from pathlib import Path
    with patch("app.config.CONFIG_PATH", Path("/nonexistent/path/firstlight.yaml")):
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()
        response = client.get("/")
    assert response.status_code == 302
    assert "/setup/1" in response.headers["Location"]
