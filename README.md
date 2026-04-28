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
