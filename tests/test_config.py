import pytest
import yaml
from pathlib import Path
from unittest.mock import patch
from importlib import reload

import app.config as cfg_mod


@pytest.fixture(autouse=True)
def reset_config_module():
    yield
    reload(cfg_mod)


def test_load_returns_defaults_when_no_file(tmp_path):
    with patch("app.config.CONFIG_PATH", tmp_path / "missing.yaml"):
        reload(cfg_mod)
        cfg = cfg_mod.load()
    assert cfg["firstlight"]["setup_complete"] is False
    assert cfg["firstlight"]["paper_size"] == "letter"
    assert cfg["location"]["lat"] == 0.0
    assert cfg["weather"]["units"] == "imperial"
    assert cfg["quote"]["enabled"] is True
    assert cfg["archive"]["retention_days"] == 30
    assert cfg["email"]["smtp_port"] == 587


def test_load_merges_partial_config(tmp_path):
    config_file = tmp_path / "firstlight.yaml"
    config_file.write_text(yaml.dump({
        "firstlight": {"setup_complete": True, "print_time": "07:00"},
        "location": {"city": "Portland", "lat": 45.52, "lon": -122.68},
    }))
    with patch("app.config.CONFIG_PATH", config_file):
        reload(cfg_mod)
        cfg = cfg_mod.load()
    assert cfg["firstlight"]["setup_complete"] is True
    assert cfg["firstlight"]["print_time"] == "07:00"
    assert cfg["firstlight"]["paper_size"] == "letter"  # filled from defaults
    assert cfg["location"]["city"] == "Portland"
    assert cfg["weather"]["units"] == "imperial"  # filled from defaults


def test_save_and_reload(tmp_path):
    config_file = tmp_path / "firstlight.yaml"
    with patch("app.config.CONFIG_PATH", config_file):
        reload(cfg_mod)
        cfg = cfg_mod.load()
        cfg["firstlight"]["print_time"] = "08:15"
        cfg_mod.save(cfg)
        cfg2 = cfg_mod.load()
    assert cfg2["firstlight"]["print_time"] == "08:15"


def test_save_creates_parent_dirs(tmp_path):
    config_file = tmp_path / "nested" / "dir" / "firstlight.yaml"
    with patch("app.config.CONFIG_PATH", config_file):
        reload(cfg_mod)
        cfg = cfg_mod.load()
        cfg_mod.save(cfg)
    assert config_file.exists()
