import copy
import sys
import yaml
from pathlib import Path

# Guard against reload() overwriting a value patched by tests.
if not hasattr(sys.modules[__name__], "CONFIG_PATH"):
    CONFIG_PATH = Path("/app/config/firstlight.yaml")

DEFAULT_CONFIG = {
    "firstlight": {
        "setup_complete": False,
        "paper_size": "letter",
        "timezone": "America/Los_Angeles",
        "print_time": "06:30",
        "printer": "Firstlight",
        "printer_ip": "",
    },
    "location": {"city": "", "lat": 0.0, "lon": 0.0},
    "weather": {"units": "imperial", "show_aqi": True, "show_rain_forecast": True},
    "quote": {"enabled": True},
    "archive": {"enabled": True, "retention_days": 30},
    "email": {
        "enabled": False,
        "smtp_host": "",
        "smtp_port": 587,
        "smtp_user": "",
        "smtp_password": "",
        "from_address": "",
        "to_address": "",
    },
    "calendar": {
        "enabled": False,
        "google_credentials": "",
        "calendar_ids": ["primary"],
    },
    "history": {"enabled": True},
    "sports": {
        "mlb": [], "nfl": [], "nba": [], "nhl": [],
        "wnba": [], "nwsl": [], "mls": [], "premier_league": [],
    },
    "news": {"max_age_hours": 24, "max_items": 15, "feeds": []},
    "tasks": {
        "source": "builtin",
        "file_path": "/tasks/tasks.txt",
        "api_url": "",
        "api_key": "",
        "api_filter": "",
    },
}


def load() -> dict:
    if not CONFIG_PATH.exists():
        return copy.deepcopy(DEFAULT_CONFIG)
    with open(CONFIG_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return _deep_merge(DEFAULT_CONFIG, data)


def save(config: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False)


def _deep_merge(base: dict, override: dict) -> dict:
    result = copy.deepcopy(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result
