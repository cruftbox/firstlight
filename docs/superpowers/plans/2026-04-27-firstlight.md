# Firstlight Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-extended-cc:subagent-driven-development (recommended) or superpowers-extended-cc:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a self-hosted personal daily digest app that renders weather, calendar, sports, news, quotes, and todos into a print-ready PDF and delivers it via printer and/or email on a schedule.

**Architecture:** Flask app with APScheduler for scheduled jobs, WeasyPrint for PDF generation, and a 10-step setup wizard. All data providers fail gracefully — a provider error never aborts the digest. All runtime state is persisted in a Docker volume at `/app/config/`.

**Tech Stack:** Flask, APScheduler, WeasyPrint, Jinja2, feedparser, PyYAML, Open-Meteo API (free/keyless), ZenQuotes API (free/keyless), ESPN API (https), Google Calendar API, Python stdlib smtplib, Bootstrap 5 (CDN), Docker + Docker Compose.

---

### Task 1: Project Scaffold & Docker Config

**Goal:** Create the complete directory structure, Docker files, requirements, and .gitignore so `docker compose build` succeeds and all key libraries import correctly.

**Files:**
- Create: `.gitignore`
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `requirements.txt`
- Create: `app/__init__.py` (empty stub)
- Create: `app/config.py` (empty stub)
- Create: `app/routes/__init__.py`
- Create: `app/providers/__init__.py`
- Create: `app/print/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/test_config.py` (empty stub)
- Create: `config/.gitkeep`

**Acceptance Criteria:**
- [ ] `docker compose build` completes without error
- [ ] `docker compose run --rm firstlight python -c "import flask; import weasyprint; import apscheduler"` exits 0
- [ ] `config/` directory is not committed (covered by .gitignore)

**Verify:** `docker compose build` → `Successfully built` with no errors

**Steps:**

- [ ] **Step 1: Create .gitignore**

```
# Python
__pycache__/
*.pyc
*.pyo
.env
.venv/
*.egg-info/

# Config volume (never commit — contains credentials)
config/

# Editor
.vscode/
.idea/
*.swp
```

- [ ] **Step 2: Create requirements.txt**

```
flask>=3.0
apscheduler>=3.10
weasyprint>=61.0
jinja2>=3.1
feedparser>=6.0
pyyaml>=6.0
requests>=2.31
pytz>=2024.1
google-auth>=2.29
google-auth-oauthlib>=1.2
google-api-python-client>=2.131
pytest>=8.0
pytest-mock>=3.14
responses>=0.25
```

- [ ] **Step 3: Create Dockerfile**

```dockerfile
FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    cups-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
COPY tests/ ./tests/

EXPOSE 5000
CMD ["python", "-m", "flask", "--app", "app", "run", "--host=0.0.0.0"]
```

- [ ] **Step 4: Create docker-compose.yml**

```yaml
services:
  firstlight:
    build: .
    container_name: firstlight
    ports:
      - "5000:5000"
    volumes:
      - ./config:/app/config
    restart: unless-stopped
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY:-changeme}
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

- [ ] **Step 5: Create stub Python files**

Create `app/__init__.py`:
```python
from flask import Flask

def create_app():
    app = Flask(__name__)
    return app
```

Create `app/config.py` — empty for now (implemented in Task 2):
```python
```

Create `app/routes/__init__.py`, `app/providers/__init__.py`, `app/print/__init__.py`, `tests/__init__.py` — all empty files.

Create `tests/test_config.py` — empty stub:
```python
```

- [ ] **Step 6: Create config/.gitkeep**

Create an empty file at `config/.gitkeep`. The `.gitignore` covers `config/` so this file won't be committed.

- [ ] **Step 7: Build and verify**

Run: `docker compose build`
Expected: build completes with no errors.

Run: `docker compose run --rm firstlight python -c "import flask; import weasyprint; import apscheduler; print('OK')"`
Expected: `OK`

- [ ] **Step 8: Commit**

```bash
git init
git add .gitignore Dockerfile docker-compose.yml requirements.txt app/ tests/
git commit -m "feat: project scaffold and Docker config"
```

---

### Task 2: Config Module

**Goal:** Implement `app/config.py` — load, save, and deep-merge YAML config with full defaults — with tests covering all cases.

**Files:**
- Modify: `app/config.py`
- Modify: `tests/test_config.py`

**Acceptance Criteria:**
- [ ] `load()` returns complete defaults when config file doesn't exist
- [ ] `load()` deep-merges partial YAML with defaults (missing keys filled in from defaults)
- [ ] `save()` writes valid YAML that round-trips correctly
- [ ] `save()` creates parent directories if they don't exist
- [ ] All tests pass

**Verify:** `docker compose run --rm firstlight pytest tests/test_config.py -v` → all PASSED

**Steps:**

- [ ] **Step 1: Write failing tests**

Replace `tests/test_config.py`:
```python
import pytest
import yaml
from pathlib import Path
from unittest.mock import patch
from importlib import reload


def test_load_returns_defaults_when_no_file(tmp_path):
    with patch("app.config.CONFIG_PATH", tmp_path / "missing.yaml"):
        import app.config as cfg_mod
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
        import app.config as cfg_mod
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
        import app.config as cfg_mod
        reload(cfg_mod)
        cfg = cfg_mod.load()
        cfg["firstlight"]["print_time"] = "08:15"
        cfg_mod.save(cfg)
        cfg2 = cfg_mod.load()
    assert cfg2["firstlight"]["print_time"] == "08:15"


def test_save_creates_parent_dirs(tmp_path):
    config_file = tmp_path / "nested" / "dir" / "firstlight.yaml"
    with patch("app.config.CONFIG_PATH", config_file):
        import app.config as cfg_mod
        reload(cfg_mod)
        cfg = cfg_mod.load()
        cfg_mod.save(cfg)
    assert config_file.exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `docker compose run --rm firstlight pytest tests/test_config.py -v`
Expected: errors (ImportError or similar — config.py is empty)

- [ ] **Step 3: Implement app/config.py**

```python
import copy
import yaml
from pathlib import Path

CONFIG_PATH = Path("/app/config/firstlight.yaml")

DEFAULT_CONFIG = {
    "firstlight": {
        "setup_complete": False,
        "paper_size": "letter",
        "timezone": "America/Los_Angeles",
        "print_time": "06:30",
        "printer": "",
    },
    "location": {"city": "", "lat": 0.0, "lon": 0.0},
    "weather": {"units": "imperial"},
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
    "sports": {
        "mlb": [], "nfl": [], "nba": [],
        "wnba": [], "mls": [], "premier_league": [],
    },
    "news": {"max_age_hours": 24, "max_items": 10, "feeds": []},
}


def load() -> dict:
    if not CONFIG_PATH.exists():
        return copy.deepcopy(DEFAULT_CONFIG)
    with open(CONFIG_PATH) as f:
        data = yaml.safe_load(f) or {}
    return _deep_merge(DEFAULT_CONFIG, data)


def save(config: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def _deep_merge(base: dict, override: dict) -> dict:
    result = copy.deepcopy(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `docker compose run --rm firstlight pytest tests/test_config.py -v`
Expected: 4 tests PASSED

- [ ] **Step 5: Commit**

```bash
git add app/config.py tests/test_config.py
git commit -m "feat: config module with YAML load/save and deep-merge defaults"
```

---

### Task 3: Flask App Factory + Base Templates

**Goal:** Wire up the Flask app factory with blueprint registration, first-run redirect, and create the shared `base.html` and `setup/base.html` templates along with a no-op scheduler stub.

**Files:**
- Modify: `app/__init__.py`
- Create: `app/scheduler.py` (no-op stub — replaced in Task 15)
- Create: `app/routes/setup.py` (stub — just `/setup/1` GET)
- Create: `app/routes/main.py` (stub — just `/` GET)
- Create: `app/routes/archive.py` (stub)
- Create: `app/routes/todo.py` (stub)
- Create: `app/templates/base.html`
- Create: `app/templates/setup/base.html`
- Create: `app/templates/index.html` (placeholder)
- Create: `app/templates/settings.html` (placeholder)
- Create: `app/templates/setup/step1_welcome.html`
- Create: `app/static/css/app.css`

**Acceptance Criteria:**
- [ ] `docker compose up -d` starts without error
- [ ] `curl http://localhost:5000/` redirects to `/setup/1` (302) when setup incomplete
- [ ] `/setup/1` returns 200 with Bootstrap navbar

**Verify:** `docker compose run --rm firstlight python -c "from app import create_app; app = create_app(); print('OK')"` → `OK`

**Steps:**

- [ ] **Step 1: Create app/scheduler.py (no-op stub)**

```python
def start_scheduler(app) -> None:
    pass

def reschedule(print_time: str, timezone: str) -> None:
    pass
```

- [ ] **Step 2: Implement app/__init__.py**

```python
import os
from flask import Flask, redirect, url_for, request


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "changeme")

    from app.routes.setup import setup_bp
    from app.routes.main import main_bp
    from app.routes.archive import archive_bp
    from app.routes.todo import todo_bp

    app.register_blueprint(setup_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(archive_bp)
    app.register_blueprint(todo_bp)

    @app.before_request
    def check_setup():
        from app.config import load as load_config
        if request.path.startswith("/setup") or request.path.startswith("/static"):
            return
        cfg = load_config()
        if not cfg["firstlight"]["setup_complete"]:
            return redirect(url_for("setup.step1"))

    from app.config import load as load_config
    cfg = load_config()
    if cfg["firstlight"]["setup_complete"]:
        from app.scheduler import start_scheduler
        start_scheduler(app)

    return app
```

- [ ] **Step 3: Create stub route files**

Create `app/routes/setup.py`:
```python
from flask import Blueprint, render_template

setup_bp = Blueprint("setup", __name__, url_prefix="/setup")


@setup_bp.route("/1")
def step1():
    return render_template("setup/step1_welcome.html")
```

Create `app/routes/main.py`:
```python
from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/settings")
def settings():
    return render_template("settings.html")
```

Create `app/routes/archive.py`:
```python
from flask import Blueprint

archive_bp = Blueprint("archive", __name__)
```

Create `app/routes/todo.py`:
```python
from flask import Blueprint

todo_bp = Blueprint("todo", __name__)
```

- [ ] **Step 4: Create app/templates/base.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}Firstlight{% endblock %}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="{{ url_for('static', filename='css/app.css') }}">
</head>
<body>
  <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
    <div class="container">
      <a class="navbar-brand fw-bold" href="/">☀ Firstlight</a>
      <div class="navbar-nav ms-auto">
        <a class="nav-link" href="/">Home</a>
        <a class="nav-link" href="/todo">To-Do</a>
        <a class="nav-link" href="/archive">Archive</a>
        <a class="nav-link" href="/settings">Settings</a>
      </div>
    </div>
  </nav>
  <div class="container mt-4">
    {% block content %}{% endblock %}
  </div>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
  {% block scripts %}{% endblock %}
</body>
</html>
```

- [ ] **Step 5: Create app/templates/setup/base.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Firstlight Setup — {% block step_title %}{% endblock %}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="{{ url_for('static', filename='css/app.css') }}">
</head>
<body class="bg-light">
  <div class="container py-5" style="max-width: 640px;">
    <div class="text-center mb-4">
      <h1 class="display-6 fw-bold">☀ Firstlight Setup</h1>
      <p class="text-muted">Step {% block step_num %}{% endblock %} of 10</p>
      <div class="progress mb-3" style="height: 6px;">
        <div class="progress-bar" style="width: {% block progress_pct %}10{% endblock %}%"></div>
      </div>
    </div>
    <div class="card shadow-sm">
      <div class="card-body p-4">
        <h4 class="card-title mb-3">{% block step_title %}{% endblock %}</h4>
        {% block content %}{% endblock %}
      </div>
    </div>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
```

- [ ] **Step 6: Create placeholder app/templates/index.html**

```html
{% extends "base.html" %}
{% block title %}Firstlight{% endblock %}
{% block content %}
<h2>Dashboard</h2>
<p class="text-muted">Coming soon.</p>
{% endblock %}
```

- [ ] **Step 7: Create placeholder app/templates/settings.html**

```html
{% extends "base.html" %}
{% block title %}Settings — Firstlight{% endblock %}
{% block content %}
<h2>Settings</h2>
<p class="text-muted">Coming soon.</p>
{% endblock %}
```

- [ ] **Step 8: Create app/templates/setup/step1_welcome.html**

```html
{% extends "setup/base.html" %}
{% block step_num %}1{% endblock %}
{% block progress_pct %}10{% endblock %}
{% block step_title %}Welcome to Firstlight{% endblock %}
{% block content %}
<p class="text-muted">Let's get your daily digest set up. This takes about 5 minutes.</p>
<form method="POST" action="/setup/1">
  <div class="mb-3">
    <label class="form-label fw-semibold">Paper size</label>
    <select name="paper_size" class="form-select">
      <option value="letter">Letter (US, 8.5×11")</option>
      <option value="a4">A4 (International, 210×297mm)</option>
    </select>
  </div>
  <button type="submit" class="btn btn-primary w-100">Continue →</button>
</form>
{% endblock %}
```

- [ ] **Step 9: Create app/static/css/app.css**

```css
body {
  font-family: system-ui, -apple-system, sans-serif;
}
.navbar-brand {
  letter-spacing: 0.05em;
}
```

- [ ] **Step 10: Verify the app starts**

Run: `docker compose up -d --build`
Run: `docker compose logs firstlight`
Expected: Flask dev server on port 5000, no errors.

Open `http://localhost:5000/` in a browser — should redirect to `http://localhost:5000/setup/1` and show the Welcome step with Bootstrap styling.

- [ ] **Step 11: Commit**

```bash
git add app/__init__.py app/scheduler.py app/routes/ app/templates/ app/static/
git commit -m "feat: Flask app factory, blueprints, first-run redirect, base templates"
```

---

### Task 4: Setup Wizard (Steps 1–10)

**Goal:** Implement all 10 setup wizard steps — route handlers, forms, and templates — that progressively configure `firstlight.yaml`.

**Files:**
- Modify: `app/routes/setup.py`
- Modify: `app/templates/setup/step1_welcome.html` (add POST handling note — already has form)
- Create: `app/templates/setup/step2_location.html`
- Create: `app/templates/setup/step3_printtime.html`
- Create: `app/templates/setup/step4_printer.html`
- Create: `app/templates/setup/step5_quote.html`
- Create: `app/templates/setup/step6_calendar.html`
- Create: `app/templates/setup/step7_sports.html`
- Create: `app/templates/setup/step8_news.html`
- Create: `app/templates/setup/step9_email.html`
- Create: `app/templates/setup/step10_review.html`

**Acceptance Criteria:**
- [ ] Completing all 10 steps sets `setup_complete: true` in config
- [ ] Each step saves its data to `firstlight.yaml` before advancing
- [ ] "Skip" buttons on steps 4, 6, 9 advance without saving data for that step
- [ ] Step 2 geocodes the city via Open-Meteo and shows lat/lon for confirmation before saving
- [ ] Step 9 "Send test email" button POSTs to `/setup/9/test-email` and shows result inline
- [ ] After step 10, `/` no longer redirects to `/setup/1`

**Verify:** Manual — complete the full wizard in the browser. Then run: `docker compose run --rm firstlight python -c "from app.config import load; c=load(); print(c['firstlight']['setup_complete'])"` → `True`

**Steps:**

- [ ] **Step 1: Implement app/routes/setup.py (all 10 steps)**

```python
from flask import Blueprint, render_template, request, redirect, url_for, session
from app.config import load as load_config, save as save_config

setup_bp = Blueprint("setup", __name__, url_prefix="/setup")


@setup_bp.route("/1", methods=["GET", "POST"])
def step1():
    cfg = load_config()
    if request.method == "POST":
        cfg["firstlight"]["paper_size"] = request.form.get("paper_size", "letter")
        save_config(cfg)
        return redirect(url_for("setup.step2"))
    return render_template("setup/step1_welcome.html", config=cfg)


@setup_bp.route("/2", methods=["GET", "POST"])
def step2():
    cfg = load_config()
    geocode_result = session.get("geocode_result")
    error = None
    if request.method == "POST":
        action = request.form.get("action")
        if action == "search":
            from app.providers.weather import geocode
            city = request.form.get("city", "").strip()
            result = geocode(city)
            if result:
                session["geocode_result"] = result
                geocode_result = result
            else:
                error = f'City "{city}" not found. Try a different name or spelling.'
        elif action == "confirm":
            result = session.pop("geocode_result", None)
            if result:
                cfg["location"]["city"] = result["name"]
                cfg["location"]["lat"] = result["lat"]
                cfg["location"]["lon"] = result["lon"]
                save_config(cfg)
                return redirect(url_for("setup.step3"))
    return render_template("setup/step2_location.html", config=cfg,
                           result=geocode_result, error=error)


@setup_bp.route("/3", methods=["GET", "POST"])
def step3():
    cfg = load_config()
    if request.method == "POST":
        cfg["firstlight"]["print_time"] = request.form.get("print_time", "06:30")
        cfg["firstlight"]["timezone"] = request.form.get("timezone", "America/Los_Angeles")
        cfg["weather"]["units"] = request.form.get("units", "imperial")
        save_config(cfg)
        return redirect(url_for("setup.step4"))
    import pytz
    return render_template("setup/step3_printtime.html", config=cfg,
                           timezones=pytz.all_timezones)


@setup_bp.route("/4", methods=["GET", "POST"])
def step4():
    cfg = load_config()
    if request.method == "POST":
        if request.form.get("action") != "skip":
            cfg["firstlight"]["printer"] = request.form.get("printer", "")
            save_config(cfg)
        return redirect(url_for("setup.step5"))
    from app.print.printer import get_printers
    return render_template("setup/step4_printer.html", config=cfg,
                           printers=get_printers())


@setup_bp.route("/5", methods=["GET", "POST"])
def step5():
    cfg = load_config()
    if request.method == "POST":
        cfg["quote"]["enabled"] = request.form.get("quote_enabled") == "on"
        save_config(cfg)
        return redirect(url_for("setup.step6"))
    preview_quote = None
    if cfg["quote"].get("enabled", True):
        from app.providers.quote import get_quote
        preview_quote = get_quote()
    return render_template("setup/step5_quote.html", config=cfg,
                           preview_quote=preview_quote)


@setup_bp.route("/6", methods=["GET", "POST"])
def step6():
    cfg = load_config()
    if request.method == "POST":
        if request.form.get("action") == "skip":
            return redirect(url_for("setup.step7"))
        creds_json = request.form.get("credentials_json", "").strip()
        if creds_json:
            from pathlib import Path
            creds_path = Path("/app/config/google_credentials.json")
            creds_path.write_text(creds_json)
            cfg["calendar"]["enabled"] = True
            save_config(cfg)
        return redirect(url_for("setup.step7"))
    return render_template("setup/step6_calendar.html", config=cfg)


@setup_bp.route("/7", methods=["GET", "POST"])
def step7():
    cfg = load_config()
    if request.method == "POST":
        for league in ["mlb", "nfl", "nba", "wnba", "mls", "premier_league"]:
            raw = request.form.get(league, "").strip()
            cfg["sports"][league] = [t.strip() for t in raw.split(",") if t.strip()]
        save_config(cfg)
        return redirect(url_for("setup.step8"))
    return render_template("setup/step7_sports.html", config=cfg)


@setup_bp.route("/8", methods=["GET", "POST"])
def step8():
    cfg = load_config()
    if request.method == "POST":
        urls = request.form.getlist("feed_url")
        labels = request.form.getlist("feed_label")
        cfg["news"]["feeds"] = [
            {"url": u.strip(), "label": l.strip()}
            for u, l in zip(urls, labels)
            if u.strip()
        ]
        cfg["news"]["max_items"] = int(request.form.get("max_items", 10))
        cfg["news"]["max_age_hours"] = int(request.form.get("max_age_hours", 24))
        save_config(cfg)
        return redirect(url_for("setup.step9"))
    return render_template("setup/step8_news.html", config=cfg)


@setup_bp.route("/9", methods=["GET", "POST"])
def step9():
    cfg = load_config()
    if request.method == "POST":
        if request.form.get("action") == "skip":
            return redirect(url_for("setup.step10"))
        cfg["email"]["enabled"] = True
        cfg["email"]["smtp_host"] = request.form.get("smtp_host", "")
        cfg["email"]["smtp_port"] = int(request.form.get("smtp_port", 587))
        cfg["email"]["smtp_user"] = request.form.get("smtp_user", "")
        cfg["email"]["smtp_password"] = request.form.get("smtp_password", "")
        cfg["email"]["from_address"] = request.form.get("from_address", "")
        cfg["email"]["to_address"] = request.form.get("to_address", "")
        save_config(cfg)
        return redirect(url_for("setup.step10"))
    return render_template("setup/step9_email.html", config=cfg)


@setup_bp.route("/9/test-email", methods=["POST"])
def test_email():
    from flask import jsonify
    from app.print.emailer import send
    from datetime import date
    data = request.get_json()
    email_config = {
        "smtp_host": data.get("smtp_host", ""),
        "smtp_port": int(data.get("smtp_port", 587)),
        "smtp_user": data.get("smtp_user", ""),
        "smtp_password": data.get("smtp_password", ""),
        "from_address": data.get("from_address", ""),
        "to_address": data.get("to_address", ""),
    }
    ok = send(b"Test email from Firstlight setup.", date.today(), email_config)
    return jsonify({"ok": ok})


@setup_bp.route("/10", methods=["GET", "POST"])
def step10():
    cfg = load_config()
    if request.method == "POST":
        cfg["firstlight"]["setup_complete"] = True
        save_config(cfg)
        from app.scheduler import start_scheduler
        from flask import current_app
        start_scheduler(current_app._get_current_object())
        return redirect(url_for("main.index"))
    return render_template("setup/step10_review.html", config=cfg)
```

- [ ] **Step 2: Create app/templates/setup/step2_location.html**

```html
{% extends "setup/base.html" %}
{% block step_num %}2{% endblock %}
{% block progress_pct %}20{% endblock %}
{% block step_title %}Your Location{% endblock %}
{% block content %}
<p class="text-muted">Used for the weather section of your digest.</p>

{% if error %}
<div class="alert alert-danger">{{ error }}</div>
{% endif %}

{% if result %}
<div class="alert alert-success">
  Found: <strong>{{ result.name }}, {{ result.country }}</strong>
  ({{ "%.4f"|format(result.lat) }}, {{ "%.4f"|format(result.lon) }})
</div>
<form method="POST">
  <input type="hidden" name="action" value="confirm">
  <button type="submit" class="btn btn-primary w-100 mb-2">Use this location →</button>
</form>
<p class="text-muted small text-center">Not right? Search again below.</p>
<hr>
{% endif %}

<form method="POST">
  <input type="hidden" name="action" value="search">
  <div class="input-group">
    <input type="text" name="city" class="form-control"
           placeholder="City name (e.g. Portland, OR)"
           value="{{ config.location.city or '' }}">
    <button type="submit" class="btn btn-outline-secondary">Search</button>
  </div>
</form>
{% endblock %}
```

- [ ] **Step 3: Create app/templates/setup/step3_printtime.html**

```html
{% extends "setup/base.html" %}
{% block step_num %}3{% endblock %}
{% block progress_pct %}30{% endblock %}
{% block step_title %}Print Time & Units{% endblock %}
{% block content %}
<form method="POST">
  <div class="mb-3">
    <label class="form-label fw-semibold">Daily print time</label>
    <input type="time" name="print_time" class="form-control"
           value="{{ config.firstlight.print_time }}">
  </div>
  <div class="mb-3">
    <label class="form-label fw-semibold">Timezone</label>
    <select name="timezone" class="form-select">
      {% for tz in timezones %}
      <option value="{{ tz }}" {% if tz == config.firstlight.timezone %}selected{% endif %}>{{ tz }}</option>
      {% endfor %}
    </select>
  </div>
  <div class="mb-3">
    <label class="form-label fw-semibold">Temperature units</label>
    <select name="units" class="form-select">
      <option value="imperial" {% if config.weather.units == 'imperial' %}selected{% endif %}>°F (Imperial)</option>
      <option value="metric" {% if config.weather.units == 'metric' %}selected{% endif %}>°C (Metric)</option>
    </select>
  </div>
  <button type="submit" class="btn btn-primary w-100">Continue →</button>
</form>
{% endblock %}
```

- [ ] **Step 4: Create app/templates/setup/step4_printer.html**

```html
{% extends "setup/base.html" %}
{% block step_num %}4{% endblock %}
{% block progress_pct %}40{% endblock %}
{% block step_title %}Printer{% endblock %}
{% block content %}
<p class="text-muted">Select a CUPS printer reachable from the container, or skip to use archive/email delivery only.</p>
<form method="POST">
  <div class="mb-3">
    <label class="form-label fw-semibold">Printer</label>
    <select name="printer" class="form-select">
      <option value="">— none —</option>
      {% for p in printers %}
      <option value="{{ p }}" {% if p == config.firstlight.printer %}selected{% endif %}>{{ p }}</option>
      {% endfor %}
    </select>
    {% if not printers %}
    <div class="form-text text-warning">No CUPS printers found. Make sure your printer is reachable from the container via <code>host.docker.internal</code>.</div>
    {% endif %}
  </div>
  <div class="d-grid gap-2">
    <button type="submit" class="btn btn-primary">Continue →</button>
    <button type="submit" name="action" value="skip" class="btn btn-outline-secondary">Skip</button>
  </div>
</form>
{% endblock %}
```

- [ ] **Step 5: Create app/templates/setup/step5_quote.html**

```html
{% extends "setup/base.html" %}
{% block step_num %}5{% endblock %}
{% block progress_pct %}50{% endblock %}
{% block step_title %}Quote of the Day{% endblock %}
{% block content %}
<p class="text-muted">A daily quote appears below the date header on your digest. No account or API key required.</p>
{% if preview_quote %}
<div class="p-3 mb-3 bg-light border rounded fst-italic text-muted small">
  "{{ preview_quote.text }}" — {{ preview_quote.author }}
</div>
{% endif %}
<form method="POST">
  <div class="form-check form-switch mb-3">
    <input class="form-check-input" type="checkbox" name="quote_enabled"
           id="quoteToggle" {% if config.quote.enabled %}checked{% endif %}>
    <label class="form-check-label" for="quoteToggle">Enable quote of the day</label>
  </div>
  <button type="submit" class="btn btn-primary w-100">Continue →</button>
</form>
{% endblock %}
```

- [ ] **Step 6: Create app/templates/setup/step6_calendar.html**

```html
{% extends "setup/base.html" %}
{% block step_num %}6{% endblock %}
{% block progress_pct %}60{% endblock %}
{% block step_title %}Google Calendar{% endblock %}
{% block content %}
<p class="text-muted">Paste your Google OAuth credentials JSON to enable calendar integration.</p>
<p class="small text-muted">In <a href="https://console.cloud.google.com/" target="_blank">Google Cloud Console</a> → APIs &amp; Services → Credentials → OAuth 2.0 Client IDs → Download JSON.</p>
<form method="POST">
  <div class="mb-3">
    <label class="form-label fw-semibold">credentials.json contents</label>
    <textarea name="credentials_json" class="form-control font-monospace" rows="6"
              placeholder='{"installed": {"client_id": "...", "client_secret": "...", ...}}'></textarea>
  </div>
  <div class="d-grid gap-2">
    <button type="submit" class="btn btn-primary">Save &amp; Continue →</button>
    <button type="submit" name="action" value="skip" class="btn btn-outline-secondary">Skip</button>
  </div>
</form>
{% endblock %}
```

- [ ] **Step 7: Create app/templates/setup/step7_sports.html**

```html
{% extends "setup/base.html" %}
{% block step_num %}7{% endblock %}
{% block progress_pct %}70{% endblock %}
{% block step_title %}Sports Teams{% endblock %}
{% block content %}
<p class="text-muted">Enter team names or abbreviations, comma-separated. Leave blank to skip a league.</p>
<form method="POST">
  {% set leagues = [
    ("mlb", "MLB Baseball", "LAD, SF, NYY"),
    ("nfl", "NFL Football", "LAR, KC, NE"),
    ("nba", "NBA Basketball", "Lakers, Celtics"),
    ("wnba", "WNBA", "Sparks, Storm"),
    ("mls", "MLS Soccer", "LAFC, Portland"),
    ("premier_league", "Premier League", "Arsenal, Chelsea"),
  ] %}
  {% for key, label, placeholder in leagues %}
  <div class="mb-2">
    <label class="form-label fw-semibold">{{ label }}</label>
    <input type="text" name="{{ key }}" class="form-control"
           placeholder="{{ placeholder }}"
           value="{{ config.sports[key] | join(', ') }}">
  </div>
  {% endfor %}
  <button type="submit" class="btn btn-primary w-100 mt-2">Continue →</button>
</form>
{% endblock %}
```

- [ ] **Step 8: Create app/templates/setup/step8_news.html**

```html
{% extends "setup/base.html" %}
{% block step_num %}8{% endblock %}
{% block progress_pct %}80{% endblock %}
{% block step_title %}News RSS Feeds{% endblock %}
{% block content %}
<p class="text-muted">Add RSS feed URLs with labels. Leave empty to skip news.</p>
<form method="POST" id="feedsForm">
  <div id="feedsList">
    {% if config.news.feeds %}
      {% for feed in config.news.feeds %}
      <div class="row g-2 mb-2 feed-row">
        <div class="col-8"><input type="text" name="feed_url" class="form-control" placeholder="https://feeds.example.com/rss" value="{{ feed.url }}"></div>
        <div class="col-3"><input type="text" name="feed_label" class="form-control" placeholder="Label" value="{{ feed.label }}"></div>
        <div class="col-1"><button type="button" class="btn btn-outline-danger btn-sm remove-feed">×</button></div>
      </div>
      {% endfor %}
    {% else %}
      <div class="row g-2 mb-2 feed-row">
        <div class="col-8"><input type="text" name="feed_url" class="form-control" placeholder="https://feeds.example.com/rss"></div>
        <div class="col-3"><input type="text" name="feed_label" class="form-control" placeholder="Label"></div>
        <div class="col-1"><button type="button" class="btn btn-outline-danger btn-sm remove-feed">×</button></div>
      </div>
    {% endif %}
  </div>
  <button type="button" class="btn btn-outline-secondary btn-sm mb-3" id="addFeed">+ Add feed</button>
  <div class="row g-2 mb-3">
    <div class="col-6">
      <label class="form-label">Max items</label>
      <input type="number" name="max_items" class="form-control" value="{{ config.news.max_items }}" min="1" max="30">
    </div>
    <div class="col-6">
      <label class="form-label">Max age (hours)</label>
      <input type="number" name="max_age_hours" class="form-control" value="{{ config.news.max_age_hours }}" min="1" max="168">
    </div>
  </div>
  <button type="submit" class="btn btn-primary w-100">Continue →</button>
</form>
<script>
document.getElementById('addFeed').addEventListener('click', function() {
  const row = document.querySelector('.feed-row').cloneNode(true);
  row.querySelectorAll('input').forEach(i => i.value = '');
  document.getElementById('feedsList').appendChild(row);
});
document.getElementById('feedsList').addEventListener('click', function(e) {
  if (e.target.classList.contains('remove-feed')) {
    const rows = document.querySelectorAll('.feed-row');
    if (rows.length > 1) e.target.closest('.feed-row').remove();
  }
});
</script>
{% endblock %}
```

- [ ] **Step 9: Create app/templates/setup/step9_email.html**

```html
{% extends "setup/base.html" %}
{% block step_num %}9{% endblock %}
{% block progress_pct %}90{% endblock %}
{% block step_title %}Email Delivery{% endblock %}
{% block content %}
<p class="text-muted">Send your digest as a PDF attachment each morning. Skip to use archive/print only.</p>
<div class="alert alert-info small">
  <strong>Gmail users:</strong> Use an App Password.
  <a href="https://myaccount.google.com/apppasswords" target="_blank">Create one here</a>,
  then use <code>smtp.gmail.com</code>, port 587, your Gmail address, and the App Password.
</div>
<form method="POST" id="emailForm">
  <div class="row g-2 mb-2">
    <div class="col-8">
      <label class="form-label">SMTP Host</label>
      <input type="text" name="smtp_host" class="form-control" placeholder="smtp.gmail.com" value="{{ config.email.smtp_host }}">
    </div>
    <div class="col-4">
      <label class="form-label">Port</label>
      <input type="number" name="smtp_port" class="form-control" value="{{ config.email.smtp_port }}">
    </div>
  </div>
  <div class="mb-2">
    <label class="form-label">Username</label>
    <input type="text" name="smtp_user" class="form-control" placeholder="you@gmail.com" value="{{ config.email.smtp_user }}">
  </div>
  <div class="mb-2">
    <label class="form-label">Password / App Password</label>
    <input type="password" name="smtp_password" class="form-control" placeholder="Leave blank to keep current">
  </div>
  <div class="row g-2 mb-3">
    <div class="col-6">
      <label class="form-label">From</label>
      <input type="email" name="from_address" class="form-control" value="{{ config.email.from_address }}">
    </div>
    <div class="col-6">
      <label class="form-label">To</label>
      <input type="email" name="to_address" class="form-control" value="{{ config.email.to_address }}">
    </div>
  </div>
  <div id="testResult" class="mb-2"></div>
  <div class="d-grid gap-2">
    <button type="button" class="btn btn-outline-secondary" id="testBtn">Send test email</button>
    <button type="submit" class="btn btn-primary">Save &amp; Continue →</button>
    <button type="submit" name="action" value="skip" class="btn btn-outline-secondary">Skip</button>
  </div>
</form>
<script>
document.getElementById('testBtn').addEventListener('click', function() {
  const f = document.getElementById('emailForm');
  fetch('/setup/9/test-email', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      smtp_host: f.smtp_host.value,
      smtp_port: parseInt(f.smtp_port.value),
      smtp_user: f.smtp_user.value,
      smtp_password: f.smtp_password.value,
      from_address: f.from_address.value,
      to_address: f.to_address.value,
    }),
  }).then(r => r.json()).then(d => {
    document.getElementById('testResult').innerHTML = d.ok
      ? '<div class="alert alert-success py-1">Test email sent!</div>'
      : '<div class="alert alert-danger py-1">Failed. Check credentials and try again.</div>';
  });
});
</script>
{% endblock %}
```

- [ ] **Step 10: Create app/templates/setup/step10_review.html**

```html
{% extends "setup/base.html" %}
{% block step_num %}10{% endblock %}
{% block progress_pct %}100{% endblock %}
{% block step_title %}Review &amp; Confirm{% endblock %}
{% block content %}
<dl class="row small">
  <dt class="col-5">Paper size</dt>
  <dd class="col-7">{{ config.firstlight.paper_size }}</dd>
  <dt class="col-5">Location</dt>
  <dd class="col-7">{{ config.location.city or '—' }}</dd>
  <dt class="col-5">Print time</dt>
  <dd class="col-7">{{ config.firstlight.print_time }} ({{ config.firstlight.timezone }})</dd>
  <dt class="col-5">Units</dt>
  <dd class="col-7">{{ config.weather.units }}</dd>
  <dt class="col-5">Printer</dt>
  <dd class="col-7">{{ config.firstlight.printer or '— none —' }}</dd>
  <dt class="col-5">Quote of the day</dt>
  <dd class="col-7">{{ 'Enabled' if config.quote.enabled else 'Disabled' }}</dd>
  <dt class="col-5">Google Calendar</dt>
  <dd class="col-7">{{ 'Enabled' if config.calendar.enabled else 'Skipped' }}</dd>
  <dt class="col-5">Sports teams</dt>
  <dd class="col-7">
    {% set teams = namespace(all=[]) %}
    {% for league, t in config.sports.items() %}{% if t %}{% set teams.all = teams.all + t %}{% endif %}{% endfor %}
    {{ teams.all | join(', ') or '— none —' }}
  </dd>
  <dt class="col-5">News feeds</dt>
  <dd class="col-7">{{ config.news.feeds | length }} feed(s)</dd>
  <dt class="col-5">Email</dt>
  <dd class="col-7">
    {% if config.email.enabled %}{{ config.email.to_address }} via {{ config.email.smtp_host }}
    {% else %}Skipped{% endif %}
  </dd>
</dl>
<form method="POST">
  <button type="submit" class="btn btn-success w-100 btn-lg mt-2">✓ Finish Setup</button>
</form>
<a href="{{ url_for('setup.step1') }}" class="btn btn-link w-100 mt-2">← Start over</a>
{% endblock %}
```

- [ ] **Step 11: Test the full wizard manually**

Run: `docker compose up -d --build`
Open `http://localhost:5000/` and walk through all 10 steps. For step 2, enter a real city. For steps 4, 6, 9, use "Skip".

After step 10, run:
`docker compose run --rm firstlight python -c "from app.config import load; c=load(); print(c['firstlight']['setup_complete'])"`
Expected: `True`

Open `http://localhost:5000/` — should show the dashboard (not redirect to setup).

- [ ] **Step 12: Commit**

```bash
git add app/routes/setup.py app/templates/setup/
git commit -m "feat: setup wizard steps 1-10"
```

---

### Task 5: Weather Provider

**Goal:** Implement `app/providers/weather.py` — Open-Meteo geocoding and forecast with 30-minute in-memory cache — with mocked HTTP tests.

**Files:**
- Create: `app/providers/weather.py`
- Create: `tests/test_providers.py`

**Acceptance Criteria:**
- [ ] `geocode("Portland")` returns `{"name": str, "lat": float, "lon": float, "country": str}`
- [ ] `geocode("zzznonsense")` returns `None`
- [ ] `get_forecast(45.52, -122.68, "imperial")` returns dict with keys: `condition`, `temp`, `high`, `low`, `units`, `hourly`
- [ ] `hourly` contains 5 entries for hours 6, 9, 12, 15, 18
- [ ] Second call within 30 minutes returns cached result (no HTTP request made)
- [ ] Returns `None` gracefully on network error
- [ ] All tests pass

**Verify:** `docker compose run --rm firstlight pytest tests/test_providers.py -v` → all PASSED

**Steps:**

- [ ] **Step 1: Write failing tests**

Create `tests/test_providers.py`:
```python
import pytest
import responses as resp_lib
from unittest.mock import patch

# ── Weather ───────────────────────────────────────────────────────────────────

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

GEOCODE_RESPONSE = {
    "results": [{"name": "Portland", "latitude": 45.52, "longitude": -122.68,
                 "country": "United States"}]
}

FORECAST_RESPONSE = {
    "current": {"temperature_2m": 68.0, "weathercode": 1, "windspeed_10m": 5.0},
    "hourly": {
        "time": [
            "2026-04-28T00:00", "2026-04-28T01:00", "2026-04-28T02:00",
            "2026-04-28T03:00", "2026-04-28T04:00", "2026-04-28T05:00",
            "2026-04-28T06:00", "2026-04-28T07:00", "2026-04-28T08:00",
            "2026-04-28T09:00", "2026-04-28T10:00", "2026-04-28T11:00",
            "2026-04-28T12:00", "2026-04-28T13:00", "2026-04-28T14:00",
            "2026-04-28T15:00", "2026-04-28T16:00", "2026-04-28T17:00",
            "2026-04-28T18:00", "2026-04-28T19:00", "2026-04-28T20:00",
            "2026-04-28T21:00", "2026-04-28T22:00", "2026-04-28T23:00",
        ],
        "temperature_2m": [
            55.0, 54.0, 53.0, 52.0, 51.0, 50.0,
            61.0, 63.0, 65.0, 67.0, 70.0, 72.0,
            74.0, 76.0, 77.0, 77.0, 76.0, 74.0,
            70.0, 68.0, 65.0, 63.0, 61.0, 59.0,
        ],
    },
    "daily": {"temperature_2m_max": [78.0], "temperature_2m_min": [50.0]},
}


@resp_lib.activate
def test_geocode_found():
    resp_lib.add(resp_lib.GET, GEOCODE_URL, json=GEOCODE_RESPONSE, status=200)
    from app.providers.weather import geocode
    result = geocode("Portland")
    assert result is not None
    assert result["name"] == "Portland"
    assert result["lat"] == 45.52
    assert result["lon"] == -122.68
    assert "country" in result


@resp_lib.activate
def test_geocode_not_found():
    resp_lib.add(resp_lib.GET, GEOCODE_URL, json={"results": []}, status=200)
    from app.providers.weather import geocode
    assert geocode("zzznonsense") is None


@resp_lib.activate
def test_get_forecast_returns_expected_keys():
    from app.providers import weather as w
    w._cache.clear()
    resp_lib.add(resp_lib.GET, FORECAST_URL, json=FORECAST_RESPONSE, status=200)
    result = w.get_forecast(45.52, -122.68, "imperial")
    assert result is not None
    assert result["condition"] == "Mainly clear"
    assert result["temp"] == 68
    assert result["high"] == 78
    assert result["low"] == 50
    assert result["units"] == "imperial"
    assert isinstance(result["hourly"], list)
    assert len(result["hourly"]) == 5  # 6am, 9am, 12pm, 3pm, 6pm


@resp_lib.activate
def test_get_forecast_uses_cache():
    from app.providers import weather as w
    w._cache.clear()
    resp_lib.add(resp_lib.GET, FORECAST_URL, json=FORECAST_RESPONSE, status=200)
    w.get_forecast(45.52, -122.68, "imperial")
    resp_lib.reset()  # remove mock — any HTTP would raise ConnectionError
    result = w.get_forecast(45.52, -122.68, "imperial")
    assert result is not None


@resp_lib.activate
def test_get_forecast_returns_none_on_error():
    from app.providers import weather as w
    w._cache.clear()
    resp_lib.add(resp_lib.GET, FORECAST_URL, body=ConnectionError("network error"))
    result = w.get_forecast(45.52, -122.68, "imperial")
    assert result is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `docker compose run --rm firstlight pytest tests/test_providers.py -v`
Expected: ImportError (weather.py doesn't exist yet)

- [ ] **Step 3: Implement app/providers/weather.py**

```python
import requests
import time
from threading import Lock

_cache: dict = {}
_cache_lock = Lock()
CACHE_TTL = 1800  # 30 minutes

WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def geocode(city: str) -> dict | None:
    """Returns {"name", "lat", "lon", "country"} or None if not found."""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    try:
        resp = requests.get(url, params={"name": city, "count": 1, "format": "json"}, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("results", [])
    except Exception:
        return None
    if not results:
        return None
    r = results[0]
    return {
        "name": r["name"],
        "lat": r["latitude"],
        "lon": r["longitude"],
        "country": r.get("country", ""),
    }


def get_forecast(lat: float, lon: float, units: str = "imperial") -> dict | None:
    """Returns weather dict or None on failure. Cached for 30 minutes."""
    cache_key = (lat, lon, units)
    with _cache_lock:
        entry = _cache.get(cache_key)
        if entry and time.time() - entry["ts"] < CACHE_TTL:
            return entry["data"]

    temp_unit = "fahrenheit" if units == "imperial" else "celsius"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,weathercode,windspeed_10m",
        "hourly": "temperature_2m,weathercode",
        "daily": "temperature_2m_max,temperature_2m_min",
        "temperature_unit": temp_unit,
        "timezone": "auto",
        "forecast_days": 1,
    }
    try:
        resp = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=10)
        resp.raise_for_status()
        raw = resp.json()
    except Exception:
        return None

    current = raw.get("current", {})
    code = current.get("weathercode", 0)
    temp = current.get("temperature_2m")
    daily = raw.get("daily", {})
    high = daily.get("temperature_2m_max", [None])[0]
    low = daily.get("temperature_2m_min", [None])[0]

    hourly_times = raw.get("hourly", {}).get("time", [])
    hourly_temps = raw.get("hourly", {}).get("temperature_2m", [])
    target_hours = [6, 9, 12, 15, 18]
    hourly_strip = []
    for h in target_hours:
        suffix = f"T{h:02d}:00"
        for i, t in enumerate(hourly_times):
            if t.endswith(suffix):
                hourly_strip.append({"hour": h, "temp": round(hourly_temps[i])})
                break

    result = {
        "condition": WMO_CODES.get(code, "Unknown"),
        "temp": round(temp) if temp is not None else None,
        "high": round(high) if high is not None else None,
        "low": round(low) if low is not None else None,
        "units": units,
        "hourly": hourly_strip,
    }

    with _cache_lock:
        _cache[cache_key] = {"ts": time.time(), "data": result}

    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `docker compose run --rm firstlight pytest tests/test_providers.py -v`
Expected: 5 tests PASSED

- [ ] **Step 5: Commit**

```bash
git add app/providers/weather.py tests/test_providers.py
git commit -m "feat: weather provider (Open-Meteo, WMO codes, 30-min cache)"
```

---

### Task 6: Quote Provider

**Goal:** Implement `app/providers/quote.py` — ZenQuotes daily quote with date-keyed in-memory cache — with tests.

**Files:**
- Create: `app/providers/quote.py`
- Modify: `tests/test_providers.py`

**Acceptance Criteria:**
- [ ] `get_quote()` returns `{"text": str, "author": str}`
- [ ] Second call on the same calendar day returns cached result without any HTTP request
- [ ] Returns `None` gracefully on network error
- [ ] All tests pass

**Verify:** `docker compose run --rm firstlight pytest tests/test_providers.py -k quote -v` → all PASSED

**Steps:**

- [ ] **Step 1: Add quote tests — append to tests/test_providers.py**

```python
# ── Quote ─────────────────────────────────────────────────────────────────────

QUOTE_URL = "https://zenquotes.io/api/today"
QUOTE_RESPONSE = [{"q": "The secret of getting ahead is getting started.", "a": "Mark Twain", "h": ""}]


@resp_lib.activate
def test_get_quote_returns_text_and_author():
    from app.providers import quote as q
    q._cache["date"] = None
    resp_lib.add(resp_lib.GET, QUOTE_URL, json=QUOTE_RESPONSE, status=200)
    result = q.get_quote()
    assert result is not None
    assert result["text"] == "The secret of getting ahead is getting started."
    assert result["author"] == "Mark Twain"


@resp_lib.activate
def test_get_quote_uses_daily_cache():
    from app.providers import quote as q
    from datetime import date
    q._cache["date"] = date.today().isoformat()
    q._cache["data"] = {"text": "cached quote", "author": "Cache Author"}
    # No mock registered — any HTTP would raise ConnectionError
    result = q.get_quote()
    assert result["text"] == "cached quote"


@resp_lib.activate
def test_get_quote_returns_none_on_error():
    from app.providers import quote as q
    q._cache["date"] = None
    resp_lib.add(resp_lib.GET, QUOTE_URL, body=ConnectionError("network"))
    assert q.get_quote() is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `docker compose run --rm firstlight pytest tests/test_providers.py -k quote -v`
Expected: ImportError (quote.py doesn't exist)

- [ ] **Step 3: Implement app/providers/quote.py**

```python
import requests
from datetime import date
from threading import Lock

_cache: dict = {"date": None, "data": None}
_cache_lock = Lock()


def get_quote() -> dict | None:
    """Returns {"text": str, "author": str} or None on failure. Cached daily."""
    today = date.today().isoformat()
    with _cache_lock:
        if _cache["date"] == today:
            return _cache["data"]

    try:
        resp = requests.get("https://zenquotes.io/api/today", timeout=10)
        resp.raise_for_status()
        items = resp.json()
        if not items:
            return None
        item = items[0]
        result = {"text": item["q"], "author": item["a"]}
    except Exception:
        return None

    with _cache_lock:
        _cache["date"] = today
        _cache["data"] = result

    return result
```

- [ ] **Step 4: Run all provider tests**

Run: `docker compose run --rm firstlight pytest tests/test_providers.py -v`
Expected: all tests PASSED

- [ ] **Step 5: Commit**

```bash
git add app/providers/quote.py tests/test_providers.py
git commit -m "feat: quote provider (ZenQuotes, daily cache)"
```

---

### Task 7: News Provider

**Goal:** Implement `app/providers/news.py` — feedparser with age filtering and title deduplication — with tests.

**Files:**
- Create: `app/providers/news.py`
- Modify: `tests/test_providers.py`

**Acceptance Criteria:**
- [ ] Returns list of `{"title", "url", "label"}` for configured feeds
- [ ] Skips entries published more than `max_age_hours` ago
- [ ] Deduplicates entries with the same title (case-insensitive hash)
- [ ] Respects `max_items` ceiling across all feeds combined
- [ ] Returns `[]` gracefully if a feed URL raises an exception
- [ ] All tests pass

**Verify:** `docker compose run --rm firstlight pytest tests/test_providers.py -k news -v` → all PASSED

**Steps:**

- [ ] **Step 1: Add news tests — append to tests/test_providers.py**

```python
# ── News ──────────────────────────────────────────────────────────────────────

from unittest.mock import patch as _patch
from datetime import datetime, timezone, timedelta


def _make_entry(title, link, hours_ago=1):
    pub = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    return {"title": title, "link": link, "published_parsed": pub.timetuple()}


def _fake_feed(entries_dicts):
    entries = [type("E", (), d)() for d in entries_dicts]
    return type("Feed", (), {"entries": entries})()


def test_get_news_returns_items():
    fake = _fake_feed([
        _make_entry("AI chip rules", "https://example.com/1"),
        _make_entry("City transit plan", "https://example.com/2"),
    ])
    with _patch("feedparser.parse", return_value=fake):
        from app.providers.news import get_news
        items = get_news([{"url": "https://example.com/rss", "label": "Tech"}],
                         max_age_hours=24, max_items=10)
    assert len(items) == 2
    assert items[0]["title"] == "AI chip rules"
    assert items[0]["label"] == "Tech"


def test_get_news_filters_old_items():
    fake = _fake_feed([
        _make_entry("Recent", "https://example.com/1", hours_ago=1),
        _make_entry("Old", "https://example.com/2", hours_ago=30),
    ])
    with _patch("feedparser.parse", return_value=fake):
        from app.providers.news import get_news
        items = get_news([{"url": "https://example.com/rss", "label": "Tech"}],
                         max_age_hours=24, max_items=10)
    assert len(items) == 1
    assert items[0]["title"] == "Recent"


def test_get_news_deduplicates():
    entry_dict = _make_entry("Same headline", "https://example.com/1")
    fake = _fake_feed([entry_dict])
    with _patch("feedparser.parse", return_value=fake):
        from app.providers.news import get_news
        items = get_news(
            [{"url": "https://a.com/rss", "label": "A"},
             {"url": "https://b.com/rss", "label": "B"}],
            max_age_hours=24, max_items=10,
        )
    assert len(items) == 1


def test_get_news_respects_max_items():
    fake = _fake_feed([_make_entry(f"Item {i}", f"https://example.com/{i}") for i in range(20)])
    with _patch("feedparser.parse", return_value=fake):
        from app.providers.news import get_news
        items = get_news([{"url": "https://example.com/rss", "label": "Tech"}],
                         max_age_hours=24, max_items=5)
    assert len(items) == 5


def test_get_news_handles_bad_feed():
    with _patch("feedparser.parse", side_effect=Exception("network error")):
        from app.providers.news import get_news
        items = get_news([{"url": "https://broken.example/rss", "label": "Bad"}],
                         max_age_hours=24, max_items=10)
    assert items == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `docker compose run --rm firstlight pytest tests/test_providers.py -k news -v`
Expected: ImportError

- [ ] **Step 3: Implement app/providers/news.py**

```python
import feedparser
import hashlib
from datetime import datetime, timedelta, timezone


def get_news(feeds: list, max_age_hours: int = 24, max_items: int = 10) -> list:
    """Returns list of {"title", "url", "label"} deduped by title, within max_age_hours."""
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

        for entry in feed.entries:
            title = getattr(entry, "title", "").strip()
            link = getattr(entry, "link", "")

            dedup_key = hashlib.md5(title.lower().encode()).hexdigest()
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            published = getattr(entry, "published_parsed", None)
            if published:
                pub_dt = datetime(*published[:6], tzinfo=timezone.utc)
                if pub_dt < cutoff:
                    continue

            items.append({"title": title, "url": link, "label": label})
            if len(items) >= max_items:
                return items

    return items
```

- [ ] **Step 4: Run all provider tests**

Run: `docker compose run --rm firstlight pytest tests/test_providers.py -v`
Expected: all tests PASSED

- [ ] **Step 5: Commit**

```bash
git add app/providers/news.py tests/test_providers.py
git commit -m "feat: news provider (feedparser, age filter, dedup)"
```

---

### Task 8: Sports Provider

**Goal:** Implement `app/providers/sports.py` — ESPN API with https endpoints, multi-team name/abbreviation matching — with tests.

**Files:**
- Create: `app/providers/sports.py`
- Modify: `tests/test_providers.py`

**Acceptance Criteria:**
- [ ] Returns list of `{"emoji", "text"}` for teams matching by name or abbreviation
- [ ] Completed games: shows "Away Score, Home Score  Final"
- [ ] Upcoming/in-progress games: shows event name and time
- [ ] Teams with no matching events: no entry in results
- [ ] Empty league config: no HTTP request made for that league
- [ ] Returns `[]` gracefully on network error
- [ ] All ESPN endpoints use `https://`
- [ ] All tests pass

**Verify:** `docker compose run --rm firstlight pytest tests/test_providers.py -k sports -v` → all PASSED

**Steps:**

- [ ] **Step 1: Add sports tests — append to tests/test_providers.py**

```python
# ── Sports ────────────────────────────────────────────────────────────────────

MLB_URL = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"

MLB_FINAL = {
    "events": [{
        "name": "Dodgers at Giants",
        "date": "2026-04-28T02:10Z",
        "status": {"type": {"name": "STATUS_FINAL", "completed": True}},
        "competitions": [{
            "competitors": [
                {"team": {"name": "Dodgers", "abbreviation": "LAD"}, "score": "4", "homeAway": "home"},
                {"team": {"name": "Giants", "abbreviation": "SF"}, "score": "2", "homeAway": "away"},
            ]
        }]
    }]
}

MLB_UPCOMING = {
    "events": [{
        "name": "Dodgers at Giants",
        "date": "2026-04-28T20:10Z",
        "status": {"type": {"name": "STATUS_SCHEDULED", "completed": False}},
        "competitions": [{
            "competitors": [
                {"team": {"name": "Dodgers", "abbreviation": "LAD"}, "score": "0", "homeAway": "home"},
                {"team": {"name": "Giants", "abbreviation": "SF"}, "score": "0", "homeAway": "away"},
            ]
        }]
    }]
}

EMPTY_SPORTS = {"mlb": [], "nfl": [], "nba": [], "wnba": [], "mls": [], "premier_league": []}


@resp_lib.activate
def test_sports_final_game():
    resp_lib.add(resp_lib.GET, MLB_URL, json=MLB_FINAL, status=200)
    from app.providers.sports import get_scores
    results = get_scores({**EMPTY_SPORTS, "mlb": ["LAD"]})
    assert len(results) == 1
    assert "Final" in results[0]["text"]
    assert "Dodgers" in results[0]["text"]
    assert results[0]["emoji"] == "⚾"


@resp_lib.activate
def test_sports_upcoming_game():
    resp_lib.add(resp_lib.GET, MLB_URL, json=MLB_UPCOMING, status=200)
    from app.providers.sports import get_scores
    results = get_scores({**EMPTY_SPORTS, "mlb": ["LAD"]})
    assert len(results) == 1
    assert "Dodgers" in results[0]["text"]
    assert "Final" not in results[0]["text"]


@resp_lib.activate
def test_sports_no_matching_team():
    resp_lib.add(resp_lib.GET, MLB_URL, json=MLB_FINAL, status=200)
    from app.providers.sports import get_scores
    results = get_scores({**EMPTY_SPORTS, "mlb": ["Yankees"]})
    assert results == []


def test_sports_empty_config():
    from app.providers.sports import get_scores
    results = get_scores(EMPTY_SPORTS)
    assert results == []  # no HTTP made — nothing to request


@resp_lib.activate
def test_sports_network_error():
    resp_lib.add(resp_lib.GET, MLB_URL, body=ConnectionError("network"))
    from app.providers.sports import get_scores
    results = get_scores({**EMPTY_SPORTS, "mlb": ["LAD"]})
    assert results == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `docker compose run --rm firstlight pytest tests/test_providers.py -k sports -v`
Expected: ImportError

- [ ] **Step 3: Implement app/providers/sports.py**

```python
import requests
from datetime import datetime

ENDPOINTS = {
    "mlb": "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard",
    "nfl": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
    "nba": "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
    "wnba": "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard",
    "mls": "https://site.api.espn.com/apis/site/v2/sports/soccer/usa.1/scoreboard",
    "premier_league": "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard",
}

SPORT_EMOJIS = {
    "mlb": "⚾", "nfl": "🏈", "nba": "🏀",
    "wnba": "🏀", "mls": "⚽", "premier_league": "⚽",
}


def get_scores(sports_config: dict) -> list:
    """Returns list of {"emoji", "text"} for configured teams."""
    results = []
    for league, teams in sports_config.items():
        if not teams:
            continue
        endpoint = ENDPOINTS.get(league)
        if not endpoint:
            continue
        try:
            resp = requests.get(endpoint, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            continue

        for event in data.get("events", []):
            competition = event.get("competitions", [{}])[0]
            competitors = competition.get("competitors", [])

            abbrevs = {c["team"]["abbreviation"].upper() for c in competitors if "team" in c}
            names = {c["team"]["name"].lower() for c in competitors if "team" in c}

            match = any(t.upper() in abbrevs or t.lower() in names for t in teams)
            if not match:
                continue

            completed = event.get("status", {}).get("type", {}).get("completed", False)

            if completed:
                home = next((c for c in competitors if c.get("homeAway") == "home"), None)
                away = next((c for c in competitors if c.get("homeAway") == "away"), None)
                if home and away:
                    text = (
                        f"{away['team']['name']} {away['score']}, "
                        f"{home['team']['name']} {home['score']}  Final"
                    )
                else:
                    text = event.get("name", "") + "  Final"
            else:
                event_date = event.get("date", "")
                if event_date:
                    dt = datetime.fromisoformat(event_date.replace("Z", "+00:00"))
                    time_str = dt.strftime("%-I:%M %p UTC")
                    text = f"{event['name']}  {time_str}"
                else:
                    text = event.get("name", "")

            results.append({"emoji": SPORT_EMOJIS.get(league, "🏆"), "text": text})

    return results
```

- [ ] **Step 4: Run all provider tests**

Run: `docker compose run --rm firstlight pytest tests/test_providers.py -v`
Expected: all tests PASSED

- [ ] **Step 5: Commit**

```bash
git add app/providers/sports.py tests/test_providers.py
git commit -m "feat: sports provider (ESPN API https, multi-team matching)"
```

---

### Task 9: Calendar Provider

**Goal:** Implement `app/providers/calendar.py` — Google Calendar OAuth with automatic token refresh — with tests covering the no-credentials and invalid-credentials cases.

**Files:**
- Create: `app/providers/calendar.py`
- Modify: `tests/test_providers.py`

**Acceptance Criteria:**
- [ ] `get_events()` returns `[]` when no token file exists
- [ ] `get_events()` returns `[]` when token file has invalid JSON
- [ ] Returns list of `{"time": str, "title": str, "all_day": bool}` when credentials valid
- [ ] Expired credentials trigger a refresh attempt; returns `[]` if refresh fails
- [ ] All tests pass

**Verify:** `docker compose run --rm firstlight pytest tests/test_providers.py -k calendar -v` → all PASSED

**Steps:**

- [ ] **Step 1: Add calendar tests — append to tests/test_providers.py**

```python
# ── Calendar ──────────────────────────────────────────────────────────────────

from unittest.mock import patch as _patch2


def test_calendar_returns_empty_when_no_token(tmp_path):
    with _patch2("app.providers.calendar.TOKEN_PATH", tmp_path / "missing_token.json"):
        from importlib import reload
        import app.providers.calendar as cal_mod
        reload(cal_mod)
        events = cal_mod.get_events(["primary"])
    assert events == []


def test_calendar_returns_empty_on_invalid_token(tmp_path):
    token_file = tmp_path / "token.json"
    token_file.write_text('{"invalid": true, "no_fields": "here"}')
    with _patch2("app.providers.calendar.TOKEN_PATH", token_file):
        from importlib import reload
        import app.providers.calendar as cal_mod
        reload(cal_mod)
        events = cal_mod.get_events(["primary"])
    assert events == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `docker compose run --rm firstlight pytest tests/test_providers.py -k calendar -v`
Expected: ImportError

- [ ] **Step 3: Implement app/providers/calendar.py**

```python
from pathlib import Path
from datetime import datetime, timezone, timedelta
import logging

TOKEN_PATH = Path("/app/config/google_token.json")
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def get_events(calendar_ids: list) -> list:
    """Returns list of {"time", "title", "all_day"} for today. Returns [] on any failure."""
    creds = _get_credentials()
    if not creds:
        return []

    try:
        from googleapiclient.discovery import build
        service = build("calendar", "v3", credentials=creds)
    except Exception as e:
        logging.error(f"Calendar API build failed: {e}")
        return []

    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    events = []

    for cal_id in calendar_ids:
        try:
            result = (
                service.events()
                .list(
                    calendarId=cal_id,
                    timeMin=today.isoformat(),
                    timeMax=tomorrow.isoformat(),
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
        except Exception as e:
            logging.error(f"Calendar fetch for {cal_id} failed: {e}")
            continue

        for item in result.get("items", []):
            start = item.get("start", {})
            if "dateTime" in start:
                dt = datetime.fromisoformat(start["dateTime"])
                time_str = dt.strftime("%-I:%M %p")
                all_day = False
            else:
                time_str = "All day"
                all_day = True
            events.append({
                "time": time_str,
                "title": item.get("summary", ""),
                "all_day": all_day,
            })

    return events


def _get_credentials():
    if not TOKEN_PATH.exists():
        return None
    try:
        from google.oauth2.credentials import Credentials
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    except Exception:
        return None

    if creds.expired and creds.refresh_token:
        try:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json())
        except Exception:
            return None

    return creds if creds.valid else None
```

- [ ] **Step 4: Run all provider tests**

Run: `docker compose run --rm firstlight pytest tests/test_providers.py -v`
Expected: all tests PASSED

- [ ] **Step 5: Commit**

```bash
git add app/providers/calendar.py tests/test_providers.py
git commit -m "feat: calendar provider (Google Calendar OAuth, token refresh)"
```

---

### Task 10: Digest Template & CSS

**Goal:** Create `digest.html` and `digest.css` — the single-page print layout with all sections including the quote line.

**Files:**
- Create: `app/templates/digest.html`
- Create: `app/static/css/digest.css`

**Acceptance Criteria:**
- [ ] Quote line renders when `quote` is provided; no blank space when `quote` is `None`
- [ ] Two-column section: Calendar on left, To-Do on right using CSS Grid
- [ ] Sports section omitted entirely when `sports` list is empty
- [ ] News section omitted entirely when `news` list is empty
- [ ] `@page` rule sets letter margins; `@page .a4` overrides for A4
- [ ] Quote line is italic, `white-space: nowrap`, truncated with `text-overflow: ellipsis`
- [ ] CSS is referenced via relative path from `base_url` so WeasyPrint can load it

**Verify:** Visual — this is validated together with the renderer in Task 11.

**Steps:**

- [ ] **Step 1: Create app/templates/digest.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <link rel="stylesheet" href="static/css/digest.css">
</head>
<body class="digest {{ 'a4' if config.firstlight.paper_size == 'a4' else 'letter' }}">

  <header>
    <div class="header-bar">
      <span class="title">FIRSTLIGHT</span>
      <span class="date-str">{{ date_str }}</span>
    </div>
    {% if quote %}
    <div class="quote-line">"{{ quote.text }}" — {{ quote.author }}</div>
    {% endif %}
  </header>

  <section class="weather-section">
    {% if weather %}
    <div class="weather-main">
      ☀ {{ weather.temp }}°&nbsp;&nbsp;
      {{ config.location.city }}&nbsp;&nbsp;&nbsp;
      High {{ weather.high }}° / Low {{ weather.low }}°&nbsp;&nbsp;&nbsp;
      {{ weather.condition }}
    </div>
    <div class="hourly-strip">
      {% for h in weather.hourly %}
      <span class="hour-chip">
        {{ (h.hour % 12) or 12 }}{{ 'am' if h.hour < 12 else 'pm' }} {{ h.temp }}°
      </span>
      {% endfor %}
    </div>
    {% endif %}
  </section>

  <div class="two-col">
    <section class="calendar-section">
      <h2>CALENDAR TODAY</h2>
      {% for event in calendar %}
      <div class="cal-event">
        <span class="cal-time">{{ event.time }}</span>
        <span class="cal-title">{{ event.title }}</span>
      </div>
      {% else %}
      <div class="empty">No events today</div>
      {% endfor %}
    </section>

    <section class="todo-section">
      <h2>TO-DO</h2>
      {% for item in todos %}
      <div class="todo-item">☐ {{ item.text }}</div>
      {% else %}
      <div class="empty">Nothing on the list</div>
      {% endfor %}
    </section>
  </div>

  {% if sports %}
  <section class="sports-section">
    <h2>SPORTS</h2>
    {% for score in sports %}
    <div class="score-item">{{ score.emoji }} {{ score.text }}</div>
    {% endfor %}
  </section>
  {% endif %}

  {% if news %}
  <section class="news-section">
    <h2>NEWS</h2>
    {% for item in news %}
    <div class="news-item">
      • {{ item.title }}
      {% if item.label %}<span class="news-label">[{{ item.label }}]</span>{% endif %}
    </div>
    {% endfor %}
  </section>
  {% endif %}

</body>
</html>
```

- [ ] **Step 2: Create app/static/css/digest.css**

```css
@page {
  size: letter;
  margin: 0.5in;
}

body.digest {
  font-family: 'DejaVu Sans', Arial, Helvetica, sans-serif;
  font-size: 10pt;
  line-height: 1.4;
  color: #000;
  margin: 0;
  padding: 0;
}

/* ── Header ── */
.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-weight: bold;
  font-size: 14pt;
  border-bottom: 2px solid #000;
  padding-bottom: 4px;
  margin-bottom: 2px;
}

.title {
  letter-spacing: 0.1em;
}

.quote-line {
  font-style: italic;
  font-size: 9pt;
  color: #444;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 6px;
}

/* ── Weather ── */
.weather-section {
  background: #f4f4f4;
  padding: 6px 8px;
  margin-bottom: 8px;
  border-left: 3px solid #333;
}

.weather-main {
  font-size: 11pt;
  margin-bottom: 3px;
}

.hour-chip {
  display: inline-block;
  margin-right: 6px;
  padding: 1px 5px;
  background: #e0e0e0;
  border-radius: 3px;
  font-size: 8.5pt;
}

/* ── Two-column ── */
.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 8px;
  border-top: 1px solid #ccc;
  border-bottom: 1px solid #ccc;
  padding: 6px 0;
}

h2 {
  font-size: 9pt;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  border-bottom: 1px solid #000;
  margin: 0 0 4px 0;
  padding-bottom: 2px;
}

.cal-event {
  display: flex;
  gap: 6px;
  margin-bottom: 2px;
  font-size: 9.5pt;
}

.cal-time {
  min-width: 58px;
  color: #555;
  font-size: 9pt;
}

.todo-item {
  margin-bottom: 2px;
  font-size: 9.5pt;
}

/* ── Sports ── */
.sports-section {
  margin-bottom: 8px;
}

.score-item {
  margin-bottom: 2px;
  font-size: 9.5pt;
}

/* ── News ── */
.news-item {
  margin-bottom: 2px;
  font-size: 9pt;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.news-label {
  color: #777;
  font-size: 8pt;
}

.empty {
  color: #999;
  font-style: italic;
  font-size: 9pt;
}

@media print {
  body {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
}
```

- [ ] **Step 3: Commit**

```bash
git add app/templates/digest.html app/static/css/digest.css
git commit -m "feat: digest print template and CSS layout"
```

---

### Task 11: PDF Renderer & /preview Route

**Goal:** Implement `app/print/renderer.py` (Jinja2 + WeasyPrint) and `app/print/pipeline.py` (data collection), then wire up the `/preview` route. Tests verify the renderer produces valid PDF bytes.

**Files:**
- Create: `app/print/renderer.py`
- Create: `app/print/pipeline.py`
- Modify: `app/routes/main.py`
- Create: `tests/test_renderer.py`

**Acceptance Criteria:**
- [ ] `render_digest(data, config)` returns `bytes` beginning with `%PDF`
- [ ] Renders with `quote=None` without error (no blank quote space)
- [ ] Renders with all sections populated without error
- [ ] `/preview` returns `Content-Type: application/pdf` and `%PDF` bytes
- [ ] All tests pass

**Verify:** `docker compose run --rm firstlight pytest tests/test_renderer.py -v` → all PASSED

**Steps:**

- [ ] **Step 1: Write failing tests**

Create `tests/test_renderer.py`:
```python
import pytest


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

MINIMAL_DATA = {
    "weather": {
        "condition": "Clear sky", "temp": 68, "high": 75, "low": 50,
        "units": "imperial", "hourly": [{"hour": 6, "temp": 55}],
    },
    "quote": {"text": "Test quote.", "author": "Tester"},
    "calendar": [],
    "sports": [],
    "news": [],
    "todos": [],
}


def test_render_returns_pdf_bytes():
    from app.print.renderer import render_digest
    pdf = render_digest(MINIMAL_DATA, MINIMAL_CONFIG)
    assert isinstance(pdf, bytes)
    assert pdf[:4] == b"%PDF"


def test_render_with_no_quote():
    from app.print.renderer import render_digest
    data = {**MINIMAL_DATA, "quote": None}
    pdf = render_digest(data, MINIMAL_CONFIG)
    assert pdf[:4] == b"%PDF"


def test_render_with_all_sections():
    from app.print.renderer import render_digest
    data = {
        **MINIMAL_DATA,
        "sports": [{"emoji": "⚾", "text": "Dodgers 4, Giants 2  Final"}],
        "news": [{"title": "Big news today", "url": "https://example.com", "label": "Tech"}],
        "todos": [{"text": "Buy milk", "done": False}],
        "calendar": [{"time": "9:00 AM", "title": "Standup", "all_day": False}],
    }
    pdf = render_digest(data, MINIMAL_CONFIG)
    assert pdf[:4] == b"%PDF"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `docker compose run --rm firstlight pytest tests/test_renderer.py -v`
Expected: ImportError (renderer.py doesn't exist)

- [ ] **Step 3: Implement app/print/renderer.py**

```python
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import pytz

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def render_digest(data: dict, config: dict) -> bytes:
    """Render digest data dict to PDF bytes via Jinja2 + WeasyPrint."""
    tz = pytz.timezone(config["firstlight"]["timezone"])
    now = datetime.now(tz)
    date_str = now.strftime("%A, %B %-d, %Y")

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("digest.html")
    html_str = template.render(
        date_str=date_str,
        config=config,
        weather=data.get("weather"),
        quote=data.get("quote"),
        calendar=data.get("calendar", []),
        sports=data.get("sports", []),
        news=data.get("news", []),
        todos=data.get("todos", []),
    )

    # base_url lets WeasyPrint resolve "static/css/digest.css" relative to app/
    base_url = str(TEMPLATES_DIR.parent) + "/"
    return HTML(string=html_str, base_url=base_url).write_pdf()
```

- [ ] **Step 4: Create app/print/pipeline.py**

```python
import logging
from pathlib import Path
import json


def collect_data(config: dict) -> dict:
    """Collect data from all providers. Each provider fails gracefully to empty/None."""
    from app.providers import weather, quote, news, sports
    from app.providers import calendar as cal_provider

    loc = config["location"]
    weather_data = None
    if loc.get("lat"):
        weather_data = weather.get_forecast(loc["lat"], loc["lon"], config["weather"]["units"])

    quote_data = None
    if config["quote"]["enabled"]:
        quote_data = quote.get_quote()

    calendar_data = []
    if config["calendar"]["enabled"]:
        calendar_data = cal_provider.get_events(config["calendar"]["calendar_ids"])

    sports_data = sports.get_scores(config["sports"])
    news_data = news.get_news(
        config["news"]["feeds"],
        config["news"]["max_age_hours"],
        config["news"]["max_items"],
    )

    return {
        "weather": weather_data,
        "quote": quote_data,
        "calendar": calendar_data,
        "sports": sports_data,
        "news": news_data,
        "todos": _load_todos(),
    }


def _load_todos() -> list:
    todos_path = Path("/app/config/todos.json")
    if not todos_path.exists():
        return []
    try:
        items = json.loads(todos_path.read_text())
        return [item for item in items if not item.get("done", False)]
    except Exception:
        return []


def run_pipeline() -> bytes:
    """Collect → render → archive/print/email. Returns PDF bytes. All errors logged, not raised."""
    from datetime import date
    from app.config import load as load_config
    from app.print.renderer import render_digest

    config = load_config()
    today = date.today()
    data = collect_data(config)
    pdf_bytes = render_digest(data, config)

    if config["archive"]["enabled"]:
        try:
            from app.print.archive import save, cleanup
            save(pdf_bytes, today)
            cleanup(config["archive"]["retention_days"])
        except Exception as e:
            logging.error(f"Archive error: {e}")

    if config["firstlight"]["printer"]:
        try:
            from app.print.printer import print_pdf
            print_pdf(pdf_bytes, config["firstlight"]["printer"])
        except Exception as e:
            logging.error(f"Printer error: {e}")

    if config["email"]["enabled"]:
        try:
            from app.print.emailer import send
            send(pdf_bytes, today, config["email"])
        except Exception as e:
            logging.error(f"Email error: {e}")

    return pdf_bytes
```

- [ ] **Step 5: Update app/routes/main.py with /preview**

```python
from flask import Blueprint, render_template, redirect, url_for, jsonify, Response, request
from app.config import load as load_config
import logging

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/preview")
def preview():
    from app.print.pipeline import collect_data
    from app.print.renderer import render_digest
    cfg = load_config()
    data = collect_data(cfg)
    pdf_bytes = render_digest(data, cfg)
    return Response(pdf_bytes, mimetype="application/pdf")


@main_bp.route("/print", methods=["POST"])
def print_digest():
    return jsonify({"status": "ok", "message": "pipeline not yet wired"})


@main_bp.route("/settings", methods=["GET", "POST"])
def settings():
    return render_template("settings.html")
```

- [ ] **Step 6: Run tests**

Run: `docker compose run --rm firstlight pytest tests/test_renderer.py -v`
Expected: 3 tests PASSED

- [ ] **Step 7: Verify /preview in browser**

Run: `docker compose up -d --build`
Complete setup wizard if needed, then navigate to `http://localhost:5000/preview`.
Expected: PDF renders in the browser showing today's date, weather (if location configured), and all other sections.

- [ ] **Step 8: Commit**

```bash
git add app/print/renderer.py app/print/pipeline.py app/routes/main.py tests/test_renderer.py
git commit -m "feat: PDF renderer, data collection pipeline, /preview route"
```

---

### Task 12: Print Archive Module

**Goal:** Implement `app/print/archive.py` — save PDFs to disk, clean up old files by date, list all archives — with tests.

**Files:**
- Create: `app/print/archive.py`
- Modify: `tests/test_renderer.py`

**Acceptance Criteria:**
- [ ] `save(pdf_bytes, date)` writes `config/archive/YYYY-MM-DD.pdf`
- [ ] `cleanup(retention_days)` deletes `.pdf` files with stems older than N days
- [ ] `list_all()` returns list of `{"date", "filename", "size_kb"}` sorted newest-first
- [ ] `save()` logs `OSError` but does not raise
- [ ] `list_all()` returns `[]` when directory doesn't exist
- [ ] All tests pass

**Verify:** `docker compose run --rm firstlight pytest tests/test_renderer.py -k archive -v` → all PASSED

**Steps:**

- [ ] **Step 1: Add archive tests — append to tests/test_renderer.py**

```python
# ── Archive ───────────────────────────────────────────────────────────────────

from datetime import date, timedelta
from unittest.mock import patch as _arch_patch


def test_archive_save_creates_file(tmp_path):
    with _arch_patch("app.print.archive.ARCHIVE_DIR", tmp_path):
        from importlib import reload
        import app.print.archive as arch
        reload(arch)
        arch.save(b"%PDF-test", date(2026, 4, 28))
    assert (tmp_path / "2026-04-28.pdf").exists()
    assert (tmp_path / "2026-04-28.pdf").read_bytes() == b"%PDF-test"


def test_archive_cleanup_removes_old(tmp_path):
    (tmp_path / "2026-01-01.pdf").write_bytes(b"old")
    (tmp_path / "2026-04-28.pdf").write_bytes(b"new")
    with _arch_patch("app.print.archive.ARCHIVE_DIR", tmp_path):
        from importlib import reload
        import app.print.archive as arch
        reload(arch)
        arch.cleanup(retention_days=30)
    assert not (tmp_path / "2026-01-01.pdf").exists()
    assert (tmp_path / "2026-04-28.pdf").exists()


def test_archive_list_all_sorted_newest_first(tmp_path):
    (tmp_path / "2026-04-26.pdf").write_bytes(b"a")
    (tmp_path / "2026-04-28.pdf").write_bytes(b"b")
    (tmp_path / "2026-04-27.pdf").write_bytes(b"c")
    with _arch_patch("app.print.archive.ARCHIVE_DIR", tmp_path):
        from importlib import reload
        import app.print.archive as arch
        reload(arch)
        files = arch.list_all()
    assert files[0]["filename"] == "2026-04-28.pdf"
    assert files[1]["filename"] == "2026-04-27.pdf"
    assert files[2]["filename"] == "2026-04-26.pdf"
    assert "size_kb" in files[0]
    assert "date" in files[0]


def test_archive_list_all_empty_when_no_dir(tmp_path):
    missing = tmp_path / "no_such_dir"
    with _arch_patch("app.print.archive.ARCHIVE_DIR", missing):
        from importlib import reload
        import app.print.archive as arch
        reload(arch)
        files = arch.list_all()
    assert files == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `docker compose run --rm firstlight pytest tests/test_renderer.py -k archive -v`
Expected: ImportError

- [ ] **Step 3: Implement app/print/archive.py**

```python
from pathlib import Path
from datetime import date, timedelta
import logging

ARCHIVE_DIR = Path("/app/config/archive")


def save(pdf_bytes: bytes, today: date) -> None:
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    path = ARCHIVE_DIR / f"{today.isoformat()}.pdf"
    try:
        path.write_bytes(pdf_bytes)
    except OSError as e:
        logging.error(f"Archive save failed: {e}")


def cleanup(retention_days: int) -> None:
    if not ARCHIVE_DIR.exists():
        return
    cutoff = date.today() - timedelta(days=retention_days)
    for pdf_file in ARCHIVE_DIR.glob("*.pdf"):
        try:
            file_date = date.fromisoformat(pdf_file.stem)
            if file_date < cutoff:
                pdf_file.unlink()
        except (ValueError, OSError) as e:
            logging.error(f"Archive cleanup error for {pdf_file}: {e}")


def list_all() -> list:
    if not ARCHIVE_DIR.exists():
        return []
    files = []
    for pdf_file in sorted(ARCHIVE_DIR.glob("*.pdf"), reverse=True):
        try:
            file_date = date.fromisoformat(pdf_file.stem)
            size_kb = round(pdf_file.stat().st_size / 1024, 1)
            files.append({
                "date": file_date.strftime("%A, %B %-d, %Y"),
                "filename": pdf_file.name,
                "size_kb": size_kb,
            })
        except (ValueError, OSError):
            continue
    return files
```

- [ ] **Step 4: Run tests**

Run: `docker compose run --rm firstlight pytest tests/test_renderer.py -k archive -v`
Expected: 4 tests PASSED

- [ ] **Step 5: Commit**

```bash
git add app/print/archive.py tests/test_renderer.py
git commit -m "feat: archive module (save, cleanup, list)"
```

---

### Task 13: Email Module

**Goal:** Implement `app/print/emailer.py` — build and send a multipart email with PDF attachment via stdlib smtplib — with tests.

**Files:**
- Create: `app/print/emailer.py`
- Modify: `tests/test_renderer.py`

**Acceptance Criteria:**
- [ ] Port 465 → uses `smtplib.SMTP_SSL` (no `starttls()` call)
- [ ] All other ports → uses `smtplib.SMTP` + `.starttls()`
- [ ] `smtp_user` empty → `login()` skipped entirely
- [ ] Subject formatted as `"Firstlight — Monday, April 28, 2026"`
- [ ] PDF attached as `firstlight-YYYY-MM-DD.pdf`
- [ ] Returns `True` on success, `False` on any exception (never raises)
- [ ] All tests pass

**Verify:** `docker compose run --rm firstlight pytest tests/test_renderer.py -k email -v` → all PASSED

**Steps:**

- [ ] **Step 1: Add email tests — append to tests/test_renderer.py**

```python
# ── Emailer ───────────────────────────────────────────────────────────────────

from unittest.mock import patch as _email_patch, MagicMock
from datetime import date as _date


def _make_email_config(port=587, user="user@example.com"):
    return {
        "smtp_host": "smtp.example.com",
        "smtp_port": port,
        "smtp_user": user,
        "smtp_password": "secret",
        "from_address": "from@example.com",
        "to_address": "to@example.com",
    }


def test_emailer_uses_starttls_for_port_587():
    mock_smtp = MagicMock()
    mock_instance = mock_smtp.return_value.__enter__.return_value
    with _email_patch("app.print.emailer.smtplib.SMTP", mock_smtp):
        from app.print.emailer import send
        result = send(b"%PDF", _date(2026, 4, 28), _make_email_config(port=587))
    assert result is True
    mock_instance.starttls.assert_called_once()
    mock_instance.login.assert_called_once_with("user@example.com", "secret")


def test_emailer_uses_smtp_ssl_for_port_465():
    mock_ssl = MagicMock()
    mock_instance = mock_ssl.return_value.__enter__.return_value
    with _email_patch("app.print.emailer.smtplib.SMTP_SSL", mock_ssl):
        from app.print.emailer import send
        result = send(b"%PDF", _date(2026, 4, 28), _make_email_config(port=465))
    assert result is True
    mock_instance.starttls.assert_not_called()


def test_emailer_skips_login_when_no_user():
    mock_smtp = MagicMock()
    mock_instance = mock_smtp.return_value.__enter__.return_value
    with _email_patch("app.print.emailer.smtplib.SMTP", mock_smtp):
        from app.print.emailer import send
        result = send(b"%PDF", _date(2026, 4, 28), _make_email_config(user=""))
    assert result is True
    mock_instance.login.assert_not_called()


def test_emailer_returns_false_on_error():
    with _email_patch("app.print.emailer.smtplib.SMTP", side_effect=ConnectionRefusedError("refused")):
        from app.print.emailer import send
        result = send(b"%PDF", _date(2026, 4, 28), _make_email_config())
    assert result is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `docker compose run --rm firstlight pytest tests/test_renderer.py -k email -v`
Expected: ImportError

- [ ] **Step 3: Implement app/print/emailer.py**

```python
import smtplib
import logging
from email.message import EmailMessage
from datetime import date


def send(pdf_bytes: bytes, today: date, email_config: dict) -> bool:
    """Send digest PDF as email attachment. Returns True on success, False on any failure."""
    date_str = today.strftime("%A, %B %-d, %Y")
    filename = f"firstlight-{today.isoformat()}.pdf"

    msg = EmailMessage()
    msg["Subject"] = f"Firstlight — {date_str}"
    msg["From"] = email_config["from_address"]
    msg["To"] = email_config["to_address"]
    msg.set_content("Your daily Firstlight digest is attached.")
    msg.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=filename,
    )

    host = email_config["smtp_host"]
    port = email_config["smtp_port"]
    user = email_config.get("smtp_user", "")
    password = email_config.get("smtp_password", "")

    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port) as smtp:
                if user:
                    smtp.login(user, password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(host, port) as smtp:
                smtp.starttls()
                if user:
                    smtp.login(user, password)
                smtp.send_message(msg)
        return True
    except Exception as e:
        logging.error(f"Email send failed: {e}")
        return False
```

- [ ] **Step 4: Run tests**

Run: `docker compose run --rm firstlight pytest tests/test_renderer.py -k email -v`
Expected: 4 tests PASSED

- [ ] **Step 5: Commit**

```bash
git add app/print/emailer.py tests/test_renderer.py
git commit -m "feat: email module (smtplib, SSL/STARTTLS auto-detect by port)"
```

---

### Task 14: Printer Module

**Goal:** Implement `app/print/printer.py` — list CUPS printers via `lpstat` and submit print jobs via `lpr`.

**Files:**
- Create: `app/print/printer.py`

**Acceptance Criteria:**
- [ ] `get_printers()` returns list of printer name strings parsed from `lpstat -p` output
- [ ] `get_printers()` returns `[]` when `lpstat` fails (CUPS not running — expected in dev)
- [ ] `print_pdf(pdf_bytes, "")` returns `False` immediately without calling `lpr`
- [ ] `print_pdf()` writes PDF to a temp file, calls `lpr -P <name> <file>`, cleans up temp file

**Verify:** `docker compose run --rm firstlight python -c "from app.print.printer import get_printers; print(get_printers())"` → `[]` (expected — no CUPS in container)

**Steps:**

- [ ] **Step 1: Implement app/print/printer.py**

```python
import subprocess
import tempfile
import os
import logging


def get_printers() -> list:
    """Returns list of CUPS printer names. Returns [] if CUPS is unavailable."""
    try:
        result = subprocess.run(
            ["lpstat", "-p"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        printers = []
        for line in result.stdout.splitlines():
            if line.startswith("printer "):
                parts = line.split()
                if len(parts) >= 2:
                    printers.append(parts[1])
        return printers
    except Exception:
        return []


def print_pdf(pdf_bytes: bytes, printer_name: str) -> bool:
    """Print PDF bytes to named CUPS printer via lpr. Returns True on success."""
    if not printer_name:
        return False

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(pdf_bytes)
            tmp_path = f.name

        result = subprocess.run(
            ["lpr", "-P", printer_name, tmp_path],
            capture_output=True,
            timeout=30,
        )
        if result.returncode != 0:
            logging.error(f"lpr failed: {result.stderr.decode()}")
            return False
        return True
    except Exception as e:
        logging.error(f"Print failed: {e}")
        return False
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
```

- [ ] **Step 2: Verify**

Run: `docker compose run --rm firstlight python -c "from app.print.printer import get_printers; print(get_printers())"`
Expected: `[]` — CUPS isn't running in the container, which is correct.

- [ ] **Step 3: Commit**

```bash
git add app/print/printer.py
git commit -m "feat: printer module (lpstat list, lpr submit)"
```

---

### Task 15: Full Print Pipeline + /print Route + Scheduler

**Goal:** Replace the no-op `app/scheduler.py` with a real APScheduler implementation, complete the `/print` route to run the full pipeline, and update the `/settings` route to save all config.

**Files:**
- Modify: `app/scheduler.py` (replace stub with real APScheduler)
- Modify: `app/routes/main.py` (complete /print and /settings)

**Acceptance Criteria:**
- [ ] `POST /print` runs `run_pipeline()` and returns `{"status": "ok"}`
- [ ] Pipeline saves to `config/archive/YYYY-MM-DD.pdf` when `archive.enabled: true`
- [ ] Scheduler fires `run_pipeline()` at the configured time daily
- [ ] `reschedule(print_time, timezone)` replaces the existing job without restarting Flask
- [ ] All pipeline errors (archive, printer, email) are logged but don't abort the pipeline

**Verify:** 
1. `docker compose up -d --build` → `docker compose logs firstlight` → no errors
2. `curl -X POST http://localhost:5000/print` → `{"status":"ok"}`
3. File `config/archive/YYYY-MM-DD.pdf` exists on disk

**Steps:**

- [ ] **Step 1: Replace app/scheduler.py with real APScheduler implementation**

```python
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler(daemon=True)


def start_scheduler(app) -> None:
    from app.config import load as load_config
    cfg = load_config()
    _add_job(cfg["firstlight"]["print_time"], cfg["firstlight"]["timezone"])
    if not scheduler.running:
        scheduler.start()


def reschedule(print_time: str, timezone: str) -> None:
    _add_job(print_time, timezone)
    if not scheduler.running:
        scheduler.start()


def _add_job(print_time: str, timezone: str) -> None:
    hour, minute = print_time.split(":")
    scheduler.add_job(
        func=_run_pipeline,
        trigger=CronTrigger(hour=int(hour), minute=int(minute), timezone=timezone),
        id="daily_digest",
        replace_existing=True,
    )


def _run_pipeline() -> None:
    from app.print.pipeline import run_pipeline
    try:
        run_pipeline()
    except Exception as e:
        logging.error(f"Scheduled pipeline error: {e}")
```

- [ ] **Step 2: Complete app/routes/main.py**

```python
from flask import Blueprint, render_template, redirect, url_for, jsonify, Response, request
from app.config import load as load_config
import logging

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    from app.scheduler import scheduler
    next_run = None
    job = scheduler.get_job("daily_digest")
    if job and job.next_run_time:
        next_run = job.next_run_time.strftime("%-I:%M %p")
    return render_template("index.html", next_run=next_run)


@main_bp.route("/preview")
def preview():
    from app.print.pipeline import collect_data
    from app.print.renderer import render_digest
    cfg = load_config()
    data = collect_data(cfg)
    pdf_bytes = render_digest(data, cfg)
    return Response(pdf_bytes, mimetype="application/pdf")


@main_bp.route("/print", methods=["POST"])
def print_digest():
    from app.print.pipeline import run_pipeline
    try:
        run_pipeline()
        return jsonify({"status": "ok"})
    except Exception as e:
        logging.error(f"Print route error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@main_bp.route("/settings", methods=["GET", "POST"])
def settings():
    from app.config import save as save_config
    from app.print.printer import get_printers
    from app.scheduler import reschedule
    import pytz

    cfg = load_config()

    if request.method == "POST":
        cfg["firstlight"]["print_time"] = request.form.get("print_time", cfg["firstlight"]["print_time"])
        cfg["firstlight"]["timezone"] = request.form.get("timezone", cfg["firstlight"]["timezone"])
        cfg["firstlight"]["printer"] = request.form.get("printer", "")
        cfg["firstlight"]["paper_size"] = request.form.get("paper_size", "letter")
        cfg["quote"]["enabled"] = request.form.get("quote_enabled") == "on"
        cfg["archive"]["enabled"] = request.form.get("archive_enabled") == "on"
        cfg["archive"]["retention_days"] = int(request.form.get("retention_days", 30))
        cfg["email"]["enabled"] = request.form.get("email_enabled") == "on"
        cfg["email"]["smtp_host"] = request.form.get("smtp_host", "")
        cfg["email"]["smtp_port"] = int(request.form.get("smtp_port", 587))
        cfg["email"]["smtp_user"] = request.form.get("smtp_user", "")
        smtp_password = request.form.get("smtp_password", "")
        if smtp_password:
            cfg["email"]["smtp_password"] = smtp_password
        cfg["email"]["from_address"] = request.form.get("from_address", "")
        cfg["email"]["to_address"] = request.form.get("to_address", "")
        save_config(cfg)
        reschedule(cfg["firstlight"]["print_time"], cfg["firstlight"]["timezone"])
        return redirect(url_for("main.settings") + "?saved=1")

    saved = request.args.get("saved") == "1"
    printers = get_printers()
    timezones = pytz.all_timezones
    return render_template("settings.html", config=cfg, printers=printers,
                           timezones=timezones, saved=saved)
```

- [ ] **Step 3: Rebuild and verify**

Run: `docker compose up -d --build`
Run: `docker compose logs firstlight`
Expected: Flask starts, APScheduler starts (if setup complete), no errors.

Run: `curl -X POST http://localhost:5000/print`
Expected: `{"status":"ok"}`
Expected: file appears at `config/archive/YYYY-MM-DD.pdf`

- [ ] **Step 4: Commit**

```bash
git add app/scheduler.py app/routes/main.py
git commit -m "feat: APScheduler daily digest job, /print route, /settings save"
```

---

### Task 16: Archive Routes & Template

**Goal:** Implement `app/routes/archive.py` and `archive.html` — list past digests and serve them for download with path-traversal protection.

**Files:**
- Modify: `app/routes/archive.py`
- Create: `app/templates/archive.html`

**Acceptance Criteria:**
- [ ] `GET /archive` returns list of past PDFs, newest first
- [ ] `GET /archive/2026-04-28.pdf` returns the file as a PDF download
- [ ] `GET /archive/../../etc/passwd` returns 404 (filename validated against `YYYY-MM-DD.pdf` pattern)
- [ ] `GET /archive/nonexistent.pdf` returns 404

**Verify:** Manual — run a print job, then visit `http://localhost:5000/archive`. One entry appears; clicking "Download" delivers the PDF.

**Steps:**

- [ ] **Step 1: Implement app/routes/archive.py**

```python
import re
from flask import Blueprint, render_template, send_file, abort
from app.print.archive import list_all, ARCHIVE_DIR

archive_bp = Blueprint("archive", __name__)

_FILENAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.pdf$")


@archive_bp.route("/archive")
def index():
    files = list_all()
    return render_template("archive.html", files=files)


@archive_bp.route("/archive/<filename>")
def download(filename):
    if not _FILENAME_RE.match(filename):
        abort(404)
    path = ARCHIVE_DIR / filename
    if not path.exists():
        abort(404)
    return send_file(path, mimetype="application/pdf",
                     as_attachment=True, download_name=filename)
```

- [ ] **Step 2: Create app/templates/archive.html**

```html
{% extends "base.html" %}
{% block title %}Archive — Firstlight{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
  <h2>Past Digests</h2>
  <a href="/" class="btn btn-outline-secondary btn-sm">← Home</a>
</div>

{% if files %}
<table class="table table-hover">
  <thead>
    <tr>
      <th>Date</th>
      <th>Size</th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    {% for f in files %}
    <tr>
      <td>{{ f.date }}</td>
      <td class="text-muted">{{ f.size_kb }} KB</td>
      <td>
        <a href="/archive/{{ f.filename }}" class="btn btn-sm btn-outline-primary">Download</a>
      </td>
    </tr>
    {% endfor %}
  </tbody>
</table>
{% else %}
<div class="text-center text-muted py-5">
  <p class="fs-5">No archived digests yet.</p>
  <p>Run a print job to create your first archive entry.</p>
  <form method="POST" action="/print" class="d-inline">
    <button type="submit" class="btn btn-primary">Print Now</button>
  </form>
</div>
{% endif %}
{% endblock %}
```

- [ ] **Step 3: Verify**

Run: `docker compose up -d --build`
Visit `http://localhost:5000/archive`.
If empty: click "Print Now", then refresh. Entry should appear.
Click "Download" — browser should download a valid PDF.

Try `http://localhost:5000/archive/../../etc/passwd` — should return 404.

- [ ] **Step 4: Commit**

```bash
git add app/routes/archive.py app/templates/archive.html
git commit -m "feat: archive routes (list and download with path-traversal protection)"
```

---

### Task 17: Dashboard, Settings & To-Do

**Goal:** Complete the web UI — full `index.html` dashboard, `settings.html` with all sections, `todo.html` + JS + API routes.

**Files:**
- Modify: `app/templates/index.html`
- Modify: `app/templates/settings.html`
- Create: `app/templates/todo.html`
- Create: `app/static/js/todo.js`
- Modify: `app/routes/todo.py`

**Acceptance Criteria:**
- [ ] Dashboard shows next scheduled print time, Print Now button (calls `/print` via fetch), Preview link, archive link
- [ ] Print Now button shows "Sent to printer!" or error message inline without page reload
- [ ] Settings page has General, Archive, and Email sections; saving shows "Settings saved." banner
- [ ] Todo page: add item (Enter key or Add button), delete item (× button), list persists across reloads
- [ ] `GET /api/todos` returns JSON list; `POST /api/todos` creates; `DELETE /api/todos` with `{"id": "..."}` deletes

**Verify:** Manual — visit each page; add/delete todos; save settings; click Print Now.

**Steps:**

- [ ] **Step 1: Replace app/templates/index.html**

```html
{% extends "base.html" %}
{% block title %}Firstlight{% endblock %}
{% block content %}
<div class="row g-4">
  <div class="col-md-6">
    <div class="card h-100">
      <div class="card-body">
        <h5 class="card-title">☀ Daily Digest</h5>
        {% if next_run %}
        <p class="text-muted">Next print: <strong>{{ next_run }}</strong></p>
        {% else %}
        <p class="text-muted">Scheduler not running (setup incomplete or no print time set).</p>
        {% endif %}
        <div class="d-grid gap-2">
          <button id="printBtn" class="btn btn-primary">Print Now</button>
          <a href="/preview" target="_blank" class="btn btn-outline-secondary">Preview PDF</a>
        </div>
        <div id="printStatus" class="mt-2"></div>
      </div>
    </div>
  </div>
  <div class="col-md-6">
    <div class="card h-100">
      <div class="card-body">
        <h5 class="card-title">Quick Links</h5>
        <ul class="list-unstyled mb-0">
          <li class="mb-1"><a href="/todo">✏ To-Do list</a></li>
          <li class="mb-1"><a href="/archive">📁 View past digests →</a></li>
          <li><a href="/settings">⚙ Settings</a></li>
        </ul>
      </div>
    </div>
  </div>
</div>
{% endblock %}
{% block scripts %}
<script>
document.getElementById('printBtn').addEventListener('click', function () {
  const btn = this;
  const status = document.getElementById('printStatus');
  btn.disabled = true;
  btn.textContent = 'Printing…';
  fetch('/print', {method: 'POST'})
    .then(r => r.json())
    .then(d => {
      status.innerHTML = d.status === 'ok'
        ? '<div class="alert alert-success py-1">Sent!</div>'
        : '<div class="alert alert-danger py-1">Error: ' + (d.message || 'unknown') + '</div>';
    })
    .catch(() => {
      status.innerHTML = '<div class="alert alert-danger py-1">Request failed.</div>';
    })
    .finally(() => {
      btn.disabled = false;
      btn.textContent = 'Print Now';
    });
});
</script>
{% endblock %}
```

- [ ] **Step 2: Replace app/templates/settings.html**

```html
{% extends "base.html" %}
{% block title %}Settings — Firstlight{% endblock %}
{% block content %}
<h2 class="mb-4">Settings</h2>

{% if saved %}
<div class="alert alert-success">Settings saved.</div>
{% endif %}

<form method="POST">

  <div class="card mb-4">
    <div class="card-header fw-bold">General</div>
    <div class="card-body">
      <div class="row g-3">
        <div class="col-md-4">
          <label class="form-label">Paper size</label>
          <select name="paper_size" class="form-select">
            <option value="letter" {% if config.firstlight.paper_size == 'letter' %}selected{% endif %}>Letter</option>
            <option value="a4" {% if config.firstlight.paper_size == 'a4' %}selected{% endif %}>A4</option>
          </select>
        </div>
        <div class="col-md-4">
          <label class="form-label">Print time</label>
          <input type="time" name="print_time" class="form-control"
                 value="{{ config.firstlight.print_time }}">
        </div>
        <div class="col-md-4">
          <label class="form-label">Timezone</label>
          <select name="timezone" class="form-select">
            {% for tz in timezones %}
            <option value="{{ tz }}" {% if tz == config.firstlight.timezone %}selected{% endif %}>{{ tz }}</option>
            {% endfor %}
          </select>
        </div>
        <div class="col-md-4">
          <label class="form-label">Printer</label>
          <select name="printer" class="form-select">
            <option value="">— none —</option>
            {% for p in printers %}
            <option value="{{ p }}" {% if p == config.firstlight.printer %}selected{% endif %}>{{ p }}</option>
            {% endfor %}
          </select>
        </div>
        <div class="col-md-4 d-flex align-items-end">
          <div class="form-check">
            <input class="form-check-input" type="checkbox" name="quote_enabled"
                   id="quoteCheck" {% if config.quote.enabled %}checked{% endif %}>
            <label class="form-check-label" for="quoteCheck">Quote of the day</label>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="card mb-4">
    <div class="card-header fw-bold">Archive</div>
    <div class="card-body">
      <div class="form-check form-switch mb-3">
        <input class="form-check-input" type="checkbox" name="archive_enabled"
               id="archiveCheck" {% if config.archive.enabled %}checked{% endif %}>
        <label class="form-check-label" for="archiveCheck">Enable PDF archive</label>
      </div>
      <div class="col-md-4">
        <label class="form-label">Retention (days)</label>
        <input type="number" name="retention_days" class="form-control"
               value="{{ config.archive.retention_days }}" min="1" max="365">
      </div>
    </div>
  </div>

  <div class="card mb-4">
    <div class="card-header fw-bold">Email Delivery</div>
    <div class="card-body">
      <div class="form-check form-switch mb-3">
        <input class="form-check-input" type="checkbox" name="email_enabled"
               id="emailCheck" {% if config.email.enabled %}checked{% endif %}>
        <label class="form-check-label" for="emailCheck">Enable email delivery</label>
      </div>
      <div class="row g-3">
        <div class="col-md-8">
          <label class="form-label">SMTP Host</label>
          <input type="text" name="smtp_host" class="form-control"
                 value="{{ config.email.smtp_host }}">
        </div>
        <div class="col-md-4">
          <label class="form-label">Port</label>
          <input type="number" name="smtp_port" class="form-control"
                 value="{{ config.email.smtp_port }}">
        </div>
        <div class="col-md-6">
          <label class="form-label">Username</label>
          <input type="text" name="smtp_user" class="form-control"
                 value="{{ config.email.smtp_user }}">
        </div>
        <div class="col-md-6">
          <label class="form-label">Password</label>
          <input type="password" name="smtp_password" class="form-control"
                 placeholder="Leave blank to keep current">
        </div>
        <div class="col-md-6">
          <label class="form-label">From</label>
          <input type="email" name="from_address" class="form-control"
                 value="{{ config.email.from_address }}">
        </div>
        <div class="col-md-6">
          <label class="form-label">To</label>
          <input type="email" name="to_address" class="form-control"
                 value="{{ config.email.to_address }}">
        </div>
      </div>
    </div>
  </div>

  <button type="submit" class="btn btn-primary px-4">Save Settings</button>
  <a href="/" class="btn btn-outline-secondary ms-2">Cancel</a>

</form>
{% endblock %}
```

- [ ] **Step 3: Implement app/routes/todo.py**

```python
from flask import Blueprint, render_template, request, jsonify
from pathlib import Path
import json
import uuid

todo_bp = Blueprint("todo", __name__)
TODOS_PATH = Path("/app/config/todos.json")


def _load() -> list:
    if not TODOS_PATH.exists():
        return []
    try:
        return json.loads(TODOS_PATH.read_text())
    except Exception:
        return []


def _save(todos: list) -> None:
    TODOS_PATH.parent.mkdir(parents=True, exist_ok=True)
    TODOS_PATH.write_text(json.dumps(todos, indent=2))


@todo_bp.route("/todo")
def index():
    return render_template("todo.html", todos=_load())


@todo_bp.route("/api/todos", methods=["GET"])
def get_todos():
    return jsonify(_load())


@todo_bp.route("/api/todos", methods=["POST"])
def create_todo():
    data = request.get_json()
    todos = _load()
    todo = {
        "id": str(uuid.uuid4()),
        "text": (data.get("text") or "").strip(),
        "done": False,
    }
    todos.append(todo)
    _save(todos)
    return jsonify(todo), 201


@todo_bp.route("/api/todos", methods=["DELETE"])
def delete_todo():
    data = request.get_json()
    todo_id = data.get("id")
    todos = [t for t in _load() if t["id"] != todo_id]
    _save(todos)
    return jsonify({"status": "ok"})
```

- [ ] **Step 4: Create app/templates/todo.html**

```html
{% extends "base.html" %}
{% block title %}To-Do — Firstlight{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
  <h2>To-Do</h2>
  <a href="/" class="btn btn-outline-secondary btn-sm">← Home</a>
</div>
<div class="row justify-content-center">
  <div class="col-md-7">
    <div class="input-group mb-3">
      <input type="text" id="newTodoInput" class="form-control"
             placeholder="Add a new item…">
      <button id="addTodoBtn" class="btn btn-primary">Add</button>
    </div>
    <ul id="todoList" class="list-group">
      {% for todo in todos %}
      <li class="list-group-item d-flex justify-content-between align-items-center"
          data-id="{{ todo.id }}">
        <span class="todo-text">{{ todo.text }}</span>
        <button class="btn btn-sm btn-outline-danger delete-btn">×</button>
      </li>
      {% endfor %}
    </ul>
  </div>
</div>
{% endblock %}
{% block scripts %}
<script src="{{ url_for('static', filename='js/todo.js') }}"></script>
{% endblock %}
```

- [ ] **Step 5: Create app/static/js/todo.js**

```javascript
document.addEventListener('DOMContentLoaded', function () {
  const input = document.getElementById('newTodoInput');
  const addBtn = document.getElementById('addTodoBtn');
  const list = document.getElementById('todoList');

  function addTodo() {
    const text = input.value.trim();
    if (!text) return;
    fetch('/api/todos', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({text}),
    })
    .then(r => r.json())
    .then(todo => {
      list.appendChild(makeTodoItem(todo));
      input.value = '';
    });
  }

  function makeTodoItem(todo) {
    const li = document.createElement('li');
    li.className = 'list-group-item d-flex justify-content-between align-items-center';
    li.dataset.id = todo.id;
    const span = document.createElement('span');
    span.className = 'todo-text';
    span.textContent = todo.text;
    const btn = document.createElement('button');
    btn.className = 'btn btn-sm btn-outline-danger delete-btn';
    btn.textContent = '×';
    li.appendChild(span);
    li.appendChild(btn);
    return li;
  }

  addBtn.addEventListener('click', addTodo);
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') addTodo();
  });

  list.addEventListener('click', function (e) {
    if (e.target.classList.contains('delete-btn')) {
      const li = e.target.closest('li');
      fetch('/api/todos', {
        method: 'DELETE',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({id: li.dataset.id}),
      }).then(() => li.remove());
    }
  });
});
```

- [ ] **Step 6: Verify manually**

Run: `docker compose up -d --build`

Visit `http://localhost:5000/` — dashboard shows Print Now, Preview, archive link.
Visit `http://localhost:5000/todo` — add an item (type + Enter), delete an item (×), reload to confirm persistence.
Visit `http://localhost:5000/settings` — change a setting, save, confirm "Settings saved." banner.
Click Print Now — confirm "Sent!" toast appears.

- [ ] **Step 7: Commit**

```bash
git add app/templates/index.html app/templates/settings.html \
        app/templates/todo.html app/static/js/todo.js app/routes/todo.py
git commit -m "feat: dashboard, settings UI, to-do page and API"
```

---

### Task 18: End-to-End Polish & Docker Deploy

**Goal:** Run the full test suite, do a complete end-to-end verification in Docker, create README and `.env.example`, and tag v1.0.0.

**Files:**
- Create: `README.md`
- Create: `.env.example`

**Acceptance Criteria:**
- [ ] `docker compose run --rm firstlight pytest tests/ -v` → all PASSED
- [ ] Full wizard completes without error
- [ ] `POST /print` creates `config/archive/YYYY-MM-DD.pdf` and returns `{"status": "ok"}`
- [ ] `/preview` returns a valid single-page PDF with today's date
- [ ] `/archive` lists the PDF with correct date and size
- [ ] README documents quick-start steps

**Verify:** `docker compose run --rm firstlight pytest tests/ -v` → all PASSED

**Steps:**

- [ ] **Step 1: Run the full test suite**

Run: `docker compose run --rm firstlight pytest tests/ -v`
Expected: all tests PASSED. Fix any failures before continuing.

- [ ] **Step 2: End-to-end run**

Run: `docker compose up --build`
Open `http://localhost:5000/` and complete the setup wizard (use a real city in step 2).
Click "Print Now" — verify `config/archive/YYYY-MM-DD.pdf` exists on disk.
Open `http://localhost:5000/archive` — verify the PDF is listed with correct date.
Open `http://localhost:5000/preview` — verify a PDF renders with today's date.
Open `http://localhost:5000/todo` — add and delete a todo item.
Open `http://localhost:5000/settings` — save, confirm banner.

- [ ] **Step 3: Create .env.example**

```
# Copy this file to .env and set a strong SECRET_KEY before deploying
SECRET_KEY=changeme-replace-with-a-long-random-string
```

- [ ] **Step 4: Create README.md**

```markdown
# Firstlight

Self-hosted daily digest — weather, calendar, sports, news, and to-dos rendered as a
print-ready PDF and delivered to your printer and/or email each morning.

## Quick Start

**Requirements:** Docker Desktop (Windows/Mac) or Docker Engine (Linux).

```bash
git clone <repo-url> firstlight
cd firstlight
cp .env.example .env
# Edit .env to set a strong SECRET_KEY
docker compose up --build
```

Open http://localhost:5000 and complete the 10-step setup wizard.

## Features

- **Weather** via Open-Meteo (free, no API key)
- **Quote of the Day** via ZenQuotes (free, no API key)
- **Google Calendar** integration (optional — paste OAuth credentials in wizard)
- **Sports scores** via ESPN API (MLB, NFL, NBA, WNBA, MLS, Premier League)
- **RSS news feeds** with age filtering
- **To-do list** with persistent JSON storage
- **PDF archive** with configurable retention (default 30 days)
- **Email delivery** (SMTP; supports Gmail App Passwords)
- **CUPS printer** integration via `lpr`

## Configuration

All config is stored in `config/firstlight.yaml` (Docker volume). The `config/` directory
contains SMTP credentials — restrict its filesystem permissions on the host.

## Deployment (QNAP NAS)

1. Copy the repo to your NAS.
2. Create `config/` with restricted permissions: `chmod 700 config/`
3. `docker compose up -d --build`

## Development

All development happens inside the container (WeasyPrint has no native Windows support):

```bash
docker compose run --rm firstlight pytest tests/ -v
docker compose up --build   # reload after code changes
```
```

- [ ] **Step 5: Final commit and tag**

```bash
git add README.md .env.example
git commit -m "feat: README, .env.example, v1.0.0"
git tag v1.0.0
```
