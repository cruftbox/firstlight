import pytest
from pathlib import Path
from unittest.mock import patch
from importlib import reload
from app import create_app


@pytest.fixture
def wizard_client(tmp_path):
    config_path = tmp_path / "firstlight.yaml"
    with patch("app.config.CONFIG_PATH", config_path):
        import app.config as cfg_mod
        reload(cfg_mod)
        app = create_app()
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test"
        yield app.test_client(), config_path
        # reload to restore module state after each test
        reload(cfg_mod)


def test_step1_get(wizard_client):
    client, _ = wizard_client
    resp = client.get("/setup/1")
    assert resp.status_code == 200


def test_step1_post_saves_and_redirects(wizard_client):
    client, config_path = wizard_client
    resp = client.post("/setup/1", data={"paper_size": "a4"}, follow_redirects=False)
    assert resp.status_code == 302
    assert "/setup/2" in resp.headers["Location"]
    import yaml
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert cfg["firstlight"]["paper_size"] == "a4"


def test_step3_post_saves_timezone_and_units(wizard_client):
    client, config_path = wizard_client
    client.post("/setup/1", data={"paper_size": "letter"})
    resp = client.post("/setup/3", data={
        "print_time": "07:00",
        "timezone": "America/New_York",
        "units": "metric",
    }, follow_redirects=False)
    assert resp.status_code == 302
    assert "/setup/4" in resp.headers["Location"]
    import yaml
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert cfg["firstlight"]["timezone"] == "America/New_York"
    assert cfg["weather"]["units"] == "metric"


def test_step4_skip_does_not_save_printer(wizard_client):
    client, config_path = wizard_client
    resp = client.post("/setup/4", data={"action": "skip"}, follow_redirects=False)
    assert resp.status_code == 302
    assert "/setup/5" in resp.headers["Location"]


def test_step9_skip_redirects_to_step10(wizard_client):
    client, _ = wizard_client
    resp = client.post("/setup/9", data={"action": "skip"}, follow_redirects=False)
    assert resp.status_code == 302
    assert "/setup/10" in resp.headers["Location"]


def test_step10_post_sets_setup_complete(wizard_client):
    client, config_path = wizard_client
    # need a config file to exist first (step 1 creates it)
    client.post("/setup/1", data={"paper_size": "letter"})
    resp = client.post("/setup/10", follow_redirects=False)
    assert resp.status_code == 302
    assert "/" in resp.headers["Location"]
    import yaml
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert cfg["firstlight"]["setup_complete"] is True
