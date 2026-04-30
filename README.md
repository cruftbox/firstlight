# Firstlight

Firstlight is a self-hosted daily digest application that delivers a personalized, print-ready morning briefing straight to your printer. Each day it pulls together local weather with hourly forecasts and air quality, your Google Calendar events, sports scores from your favorite teams across MLB, NFL, NBA, WNBA, MLS, and the Premier League, curated news headlines from RSS feeds you choose, and a to-do list you manage yourself — all rendered into a clean, single-page PDF that prints automatically at whatever time you set. A quote of the day and an "on this day in history" entry round out the digest with a touch of personality.

Firstlight runs 24/7 in Docker on any always-on home server or NAS, with a first-run setup wizard that walks you through configuration in minutes. It requires no subscriptions, no cloud accounts, and no ongoing costs — weather data comes from Open-Meteo, sports from ESPN, and news from standard RSS feeds, all free and open. A built-in web interface lets you preview the digest on demand, manage your to-do list, browse a personal archive of past digests, and trigger a print from any device on your home network. Firstlight is designed to be simple to deploy, easy to maintain, and genuinely useful every single morning.

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
- **To-do list** — built-in web UI, plain text file (e.g. Syncthing), or external REST API
- **PDF archive** with configurable retention (default 30 days)
- **Email delivery** (SMTP; supports Gmail App Passwords)
- **Network printer** via CUPS inside the container — enter your printer's IP in the wizard, no drivers needed

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
