# Firstlight — Full Application Design

**Date:** 2026-04-27
**Status:** Approved

---

## Overview

Firstlight is a self-hosted personal daily digest application. It pulls weather, calendar events, sports scores, news headlines, a quote of the day, and a to-do list — renders them into a print-ready one-page PDF — and sends it to a local network printer on a schedule each morning. It also provides a web interface for on-demand printing, digest preview, archive browsing, and to-do management.

The app runs 24/7 in Docker on a QNAP NAS (or any always-on Linux host). It is distributable via Docker Compose with a first-run setup wizard.

**Development environment:** Code is written on Windows with Docker Desktop as the only supported dev environment. WeasyPrint and CUPS have no native Windows support, so the container is the runtime for all development and testing. Bare-metal local development is not supported.

---

## Tech Stack

| Component | Library/Tool |
|-----------|-------------|
| Web framework | Flask |
| Scheduled jobs | APScheduler (runs inside Flask process) |
| PDF rendering | WeasyPrint |
| HTML templating | Jinja2 (included with Flask) |
| RSS parsing | feedparser |
| Config storage | PyYAML |
| Printing | pycups or subprocess `lpr` |
| Web UI | Bootstrap 5 (CDN) |
| Google Calendar | google-auth, google-auth-oauthlib, google-api-python-client |
| HTTP calls | requests |
| Container | Docker + Docker Compose |
| Email | Python stdlib `smtplib` + `email` (no extra dependency) |

**Docker base image:** `python:3.11-slim-bookworm` (Debian 12).

---

## Infrastructure Fixes vs Original Spec

| Item | Original | Corrected |
|------|----------|-----------|
| Docker base image | `python:3.11-slim-bullseye` | `python:3.11-slim-bookworm` |
| Docker Compose | `version: "3.8"` key present | Drop deprecated `version:` key |
| ESPN API endpoints | `http://` | `https://` |
| Weather API | OpenWeatherMap One Call 3.0 (requires paid plan for new accounts) | Open-Meteo (free, no key) |
| Geocoding | OpenWeatherMap Geocoding API | Open-Meteo Geocoding API (free, no key) |

---

## Project Structure

```
firstlight/
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── README.md
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── scheduler.py
│   ├── config.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── setup.py
│   │   ├── main.py
│   │   ├── archive.py             ← NEW
│   │   └── todo.py
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── weather.py             ← rewritten for Open-Meteo
│   │   ├── calendar.py
│   │   ├── sports.py              ← https:// fix
│   │   ├── news.py
│   │   └── quote.py               ← NEW
│   ├── print/
│   │   ├── __init__.py
│   │   ├── renderer.py
│   │   ├── printer.py
│   │   ├── archive.py             ← NEW
│   │   └── emailer.py             ← NEW
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html             ← add "View past digests" link
│   │   ├── settings.html          ← add archive + email sections
│   │   ├── todo.html
│   │   ├── archive.html           ← NEW
│   │   ├── digest.html            ← add quote line
│   │   └── setup/
│   │       ├── base.html
│   │       ├── step1_welcome.html
│   │       ├── step2_location.html
│   │       ├── step3_printtime.html
│   │       ├── step4_printer.html
│   │       ├── step5_quote.html   ← NEW (replaces step5_weather.html)
│   │       ├── step6_calendar.html
│   │       ├── step7_sports.html
│   │       ├── step8_news.html
│   │       ├── step9_email.html   ← NEW
│   │       └── step10_review.html ← was step9_review.html
│   └── static/
│       ├── css/
│       │   ├── app.css
│       │   └── digest.css         ← add quote line styles
│       └── js/
│           └── todo.js
├── config/                        ← Docker volume, never commit
│   ├── firstlight.yaml
│   ├── todos.json
│   └── archive/                   ← NEW: YYYY-MM-DD.pdf files
└── tests/
    ├── test_config.py
    ├── test_providers.py
    └── test_renderer.py
```

---

## Configuration File Schema

```yaml
firstlight:
  setup_complete: false
  paper_size: letter            # letter or a4
  timezone: America/Los_Angeles
  print_time: "06:30"
  printer: ""

location:
  city: ""
  lat: 0.0
  lon: 0.0

weather:
  units: imperial               # imperial or metric (no api_key — Open-Meteo is keyless)

quote:                          # NEW
  enabled: true

archive:                        # NEW
  enabled: true
  retention_days: 30

email:                          # NEW
  enabled: false
  smtp_host: ""
  smtp_port: 587                # 587 = STARTTLS, 465 = implicit SSL
  smtp_user: ""
  smtp_password: ""             # stored in volume, never committed
  from_address: ""
  to_address: ""

calendar:
  enabled: false
  google_credentials: ""
  calendar_ids:
    - primary

sports:
  mlb: []                       # list of team identifiers; multiple teams per league supported
  nfl: []
  nba: []
  wnba: []
  mls: []
  premier_league: []

news:
  max_age_hours: 24
  max_items: 10
  feeds: []
  # Feed entry format:
  # - url: "https://feeds.example.com/rss"
  #   label: "Tech"
```

`smtp_password` is stored in the config volume (never committed to git). The README should note that `config/` should have restricted filesystem permissions on the host.

---

## Setup Wizard — 10 Steps

| Step | Title | Notes |
|------|-------|-------|
| 1 | Welcome | Paper size: Letter or A4 |
| 2 | Location | City/zip → Open-Meteo Geocoding API → confirm lat/lon |
| 3 | Print Time | Time picker + timezone dropdown |
| 4 | Printer | CUPS printer list; skip allowed |
| 5 | Quote of the Day | Toggle on/off; show preview of quote line |
| 6 | Google Calendar | OAuth flow; skip allowed |
| 7 | Sports Teams | Searchable multi-select per league; 0+ teams per league |
| 8 | News RSS Feeds | Add feeds with labels; validate each URL; curated list |
| 9 | Email | SMTP config; skip allowed; links to App Password docs for Gmail users |
| 10 | Review & Confirm | Summary of all settings; masked credentials; "Finish Setup" |

**Step 5 — Quote of the Day:**
- Simple toggle (on by default)
- Show a live preview of how the quote line appears on the digest
- No API key or account required

**Step 9 — Email:**
- Fields: SMTP host, port (587 or 465), username, password, from address, to address
- "Send test email" button validates credentials before saving
- For users with a personal mail server: standard SMTP fields, no extra steps
- For Gmail users: note explains App Passwords with a direct link to Google's setup page
- "Skip for now" leaves `email.enabled: false`; configurable later in Settings

---

## Digest Print Layout

Single page (Letter or A4). CSS Grid with `@media print`.

```
┌─────────────────────────────────────────────────────────────┐
│ FIRSTLIGHT                        Monday, April 28, 2026    │  header bar
│ "The secret of getting ahead is getting started." — Twain   │  quote (if enabled)
├─────────────────────────────────────────────────────────────┤
│ ☀ 72°  South Pasadena    High 78° / Low 56°   Sunny        │  weather
│ [6am 61°] [9am 67°] [12pm 74°] [3pm 77°] [6pm 70°]        │  hourly strip
├──────────────────────────────┬──────────────────────────────┤
│ CALENDAR TODAY               │ TO-DO                        │  two-column
│   9:00 AM  Standup           │   □ Call insurance company   │
│   2:00 PM  Dentist           │   □ Fix gate latch           │
├──────────────────────────────┴──────────────────────────────┤
│ SPORTS                                                       │  if teams configured
│ ⚾ Dodgers 4, Giants 2    Final                             │
│ 🏀 Lakers vs Nuggets      Tonight 7:30 PM PT               │
├─────────────────────────────────────────────────────────────┤
│ NEWS                                                         │
│ • AI chip export rules tightened — Reuters        [Tech]    │
│ • City council approves transit plan — LAT        [Local]   │
└─────────────────────────────────────────────────────────────┘
```

**Quote line styling:**
- Italic, small font (same visual weight as the date)
- Format: `"Quote text." — Author`
- Truncated with ellipsis if it exceeds one line at the configured paper width
- Omitted entirely from HTML (no blank space) when `quote.enabled: false`

---

## Data Providers

### Weather — `providers/weather.py` (rewritten)

**Geocoding (Step 2):**
- Endpoint: `https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&format=json`
- Returns: `name`, `latitude`, `longitude`, `country`
- No API key required

**Forecast:**
- Endpoint: `https://api.open-meteo.com/v1/forecast`
- Params:
  ```
  latitude, longitude,
  current=temperature_2m,weathercode,windspeed_10m
  hourly=temperature_2m,weathercode
  daily=temperature_2m_max,temperature_2m_min
  temperature_unit=fahrenheit|celsius
  timezone=auto
  forecast_days=1
  ```
- Weather condition text derived from WMO weather code lookup table (small dict, bundled in `weather.py`)
- Cache result for 30 minutes
- No API key required

### Quote — `providers/quote.py` (new)

- Endpoint: `https://zenquotes.io/api/today`
- Response: `[{"q": "text", "a": "Author"}]`
- Cache: 24 hours, keyed by date (new day always fetches fresh)
- Returns `None` silently if API unreachable; digest omits the quote line
- Only called when `quote.enabled: true`

### Sports — `providers/sports.py`

Unchanged except all ESPN endpoints updated from `http://` to `https://`:
- `https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard`
- `https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard`
- `https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard`
- `https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard`
- `https://site.api.espn.com/apis/site/v2/sports/soccer/usa.1/scoreboard`
- `https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard`

Multiple teams per league are supported — each league config key holds a list.

### Calendar, News, Todo

Unchanged from original spec.

---

## Print Pipeline

```
collect_all_data()
  → weather_data    (Open-Meteo, 30-min cache)
  → calendar_data
  → sports_data
  → news_data
  → todo_data
  → quote_data      (ZenQuotes, 24-hour cache, if quote.enabled)

render_digest(data) → HTML string   (Jinja2 + digest.html)
generate_pdf(html)  → PDF bytes     (WeasyPrint)

# Post-generation:
if archive.enabled:
    archive.save(pdf_bytes, today)      → config/archive/YYYY-MM-DD.pdf
    archive.cleanup(retention_days)     → delete files older than N days

send_to_printer(pdf_bytes)              (if printer configured)

if email.enabled:
    emailer.send(pdf_bytes, today)      (SMTP, PDF as attachment)
```

All steps wrapped in try/except. Any provider failure returns an empty/default value — it does not abort the digest. Archive, printer, and email errors are logged but never raised.

### `print/archive.py`

- `save(pdf_bytes, date)` — writes to `config/archive/YYYY-MM-DD.pdf`
- `cleanup(retention_days)` — deletes `.pdf` files in archive dir older than N days
- `list_all()` — returns sorted list of `{date, filename, size_kb}` for the `/archive` route
- Errors logged silently; disk full or permission errors do not crash the pipeline

### `print/emailer.py`

- Builds `multipart/mixed` message via stdlib `smtplib` + `email`
- Subject: `Firstlight — Monday, April 28, 2026`
- Body: plain text (`"Your daily Firstlight digest is attached."`)
- Attachment: `firstlight-YYYY-MM-DD.pdf`
- TLS determined by port: 465 uses `SMTP_SSL` (implicit SSL); all other ports use `SMTP` with `starttls()` — no separate TLS toggle needed
- Errors logged silently; failed email does not abort pipeline or retry

---

## Web Interface Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Dashboard: next print time, Print Now, Preview, quick todo, links |
| `/preview` | GET | Run full pipeline, return PDF inline (no print, no archive, no email) |
| `/print` | POST | Full pipeline: archive + print + email. JSON response. |
| `/settings` | GET | Edit all settings. New sections: Archive, Email. |
| `/todo` | GET | Full to-do manager |
| `/api/todos` | GET\|POST\|DELETE | JSON CRUD for todos |
| `/archive` | GET | **NEW** — list past digests, newest first |
| `/archive/<filename>` | GET | **NEW** — download a specific PDF |

**`/archive` page:**
- Table of past digests: date, file size, download link
- Filename validated as `YYYY-MM-DD.pdf` pattern before serving (prevents path traversal)
- "View past digests →" link added to the dashboard (`/`)

**`/settings` additions:**
- Archive section: enable/disable toggle, retention days input
- Email section: enable/disable toggle, all SMTP fields, "Send test email" button

---

## APScheduler

Unchanged from original spec. Scheduler starts in the Flask app factory when `setup_complete: true`. Print time changes replace the existing job via `replace_existing=True`.

---

## Docker

### Dockerfile

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

EXPOSE 5000
CMD ["python", "-m", "flask", "--app", "app", "run", "--host=0.0.0.0"]
```

### docker-compose.yml

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

Note: `version:` key removed (deprecated in Compose v2).

---

## Build Order (Revised)

### Phase 1 — Project Skeleton
- Initialize git repo, `.gitignore`, directory structure
- `config.py` — load/save/validate YAML, handle missing file
- Flask app factory with first-run redirect
- `base.html` and `setup/base.html` (Bootstrap 5)
- Setup wizard routes and templates, Steps 1–10
- `Dockerfile`, `docker-compose.yml`, `requirements.txt`, `README.md`
- Commit: `feat: project scaffold and setup wizard`

### Phase 2 — Data Providers
- `providers/weather.py` — Open-Meteo, 30-min cache
- `providers/quote.py` — ZenQuotes, 24-hour cache
- `providers/news.py` — feedparser, age filter, dedup
- `providers/sports.py` — ESPN API (https), team filter
- `providers/calendar.py` — Google Calendar OAuth
- Unit tests for each provider with mocked HTTP responses
- Commit: `feat: data providers`

### Phase 3 — Digest Rendering
- `digest.html` — full print layout including quote line
- `digest.css` — print media query, quote line italic style
- `print/renderer.py` — Jinja2 + WeasyPrint
- `/preview` route
- Commit: `feat: digest renderer and print layout`

### Phase 4 — Print Pipeline + Archive + Email + Scheduler
- `print/archive.py` — save, cleanup, list
- `print/emailer.py` — SMTP send
- `print/printer.py` — CUPS/lpr
- `/print` route — full pipeline
- `routes/archive.py` + `archive.html`
- `scheduler.py` + integration into app factory
- Commit: `feat: print pipeline, archive, email, scheduler`

### Phase 5 — Web UI + To-Do
- `index.html` — dashboard with archive link
- `todo.html` + `todo.js` + `routes/todo.py`
- `settings.html` — all settings including archive + email sections
- Commit: `feat: web UI, to-do, settings`

### Phase 6 — Polish + Docker Deploy
- End-to-end test in Docker
- Error handling audit
- README screenshots, `.env.example`
- Tag v1.0.0
- Push to GitHub
