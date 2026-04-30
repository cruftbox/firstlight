# Firstlight

Firstlight is a self-hosted daily digest application that delivers a personalized, print-ready morning briefing straight to your printer. Each day it pulls together local weather with hourly forecasts and air quality, your Google Calendar events, sports scores from your favorite teams across MLB, NFL, NBA, WNBA, MLS, and the Premier League, curated news headlines from RSS feeds you choose, and a to-do list you manage yourself — all rendered into a clean, single-page PDF that prints automatically at whatever time you set. A quote of the day and an "on this day in history" entry round out the digest with a touch of personality.

Firstlight runs 24/7 in Docker on any always-on home server or NAS, with a first-run setup wizard that walks you through configuration in minutes. It requires no subscriptions, no cloud accounts, and no ongoing costs — weather data comes from Open-Meteo, sports from ESPN, and news from standard RSS feeds, all free and open. A built-in web interface lets you preview the digest on demand, manage your to-do list, browse a personal archive of past digests, and trigger a print from any device on your home network. Firstlight is designed to be simple to deploy, easy to maintain, and genuinely useful every single morning.

![Firstlight example digest](docs/firstlight-example-page.png)

## Before You Begin

Installation requires basic comfort with the command line — cloning a repository, editing a configuration file, and running Docker commands. You don't need to be a developer, but you should be at ease in a terminal.

The documentation includes notes for QNAP NAS deployment, which is what the author runs, but Firstlight will work on any always-on server or NAS that supports Docker. Your environment will likely differ in small ways. Server environments vary enough that the setup process sometimes needs a small adjustment from the defaults documented here. Using an LLM coding assistant (Claude, ChatGPT, or similar) during installation is genuinely recommended — it can diagnose errors specific to your environment, explain what each step does, and suggest fixes without requiring you to search through documentation.

The same applies if you want to extend Firstlight. The codebase is intentionally straightforward, and adding a new data source, changing the layout, or wiring up a service that isn't built in yet is the kind of task an LLM coding assistant handles well. If you have an idea for a feature, it's likely within reach.

## Getting Started

### 1. Prerequisites

- **Docker** — [Docker Desktop](https://www.docker.com/products/docker-desktop/) on Windows or Mac; Docker Engine on Linux or a NAS.
- **Git** — to clone the repository.
- A machine that stays on overnight, such as a home server or NAS.

### 2. Clone and configure

```bash
git clone https://github.com/cruftbox/firstlight.git firstlight
cd firstlight
cp .env.example .env
```

Open `.env` and replace `changeme-replace-with-a-long-random-string` with any long random string. This is used to secure browser sessions — it doesn't need to be memorable, just unique.

### 3. Build and start

```bash
docker compose up --build
```

The first build downloads the base image and installs dependencies — expect **3–5 minutes**. You'll see log output as it progresses. When you see a line like:

```
firstlight  | * Running on http://0.0.0.0:5000
```

Firstlight is running.

### 4. Complete the setup wizard

Open **http://localhost:5000** in your browser (or replace `localhost` with your server's IP address if running on a NAS or remote machine).

You'll be redirected to the setup wizard automatically. It covers:

| Step | What you configure |
|------|--------------------|
| 1 | Paper size |
| 2 | Location (for weather) |
| 3 | Print time and timezone |
| 4 | Network printer IP |
| 5 | Optional content — quote, history, AQI, to-do source |
| 6 | Google Calendar (optional — skip if not needed) |
| 7 | Sports teams |
| 8 | News RSS feeds |
| 9 | Email delivery (optional) |
| 10 | Review and finish |

Most steps take under a minute. Calendar setup requires a Google Cloud project — see [Google Calendar Setup](#google-calendar-setup) below if you want to enable it.

### 5. Verify it works

Once the wizard completes you'll land on the home page. Click **Preview PDF** to see what the digest looks like, or **Print Now** to send it to your printer immediately.

From this point Firstlight will print automatically every morning at the time you configured. All settings can be changed later at any time from the Settings page.

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

## Google Calendar Setup

Calendar integration is optional. To enable it you need a Google Cloud project with the Calendar API enabled and an OAuth client configured as a **Web application** (not Desktop — the redirect callback requires it).

1. Go to [Google Cloud Console](https://console.cloud.google.com/) and create or select a project.
2. **Enable the API:** APIs & Services → Library → search "Google Calendar API" → Enable.
3. **Configure consent screen:** APIs & Services → OAuth consent screen → External → add your Google account as a test user.
4. **Create credentials:** APIs & Services → Credentials → Create Credentials → OAuth client ID → **Web application**.
5. **Add redirect URI:** under "Authorized redirect URIs" add `http://<your-server-address>/setup/6/callback` — for example `http://192.168.4.27:8088/setup/6/callback`.
6. Download the JSON file and paste its contents into the setup wizard at step 6.

Google will prompt you to authorize access, then redirect back to the wizard automatically. Calendar integration remains optional — skip step 6 if you don't need it.

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
