import requests
import logging
import pytz
from datetime import datetime, timezone, timedelta

ENDPOINTS = {
    "mlb": "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard",
    "nfl": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
    "nba": "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
    "nhl": "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard",
    "wnba": "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard",
    "mls": "https://site.api.espn.com/apis/site/v2/sports/soccer/usa.1/scoreboard",
    "premier_league": "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard",
}

SPORT_EMOJIS = {
    "mlb": "⚾", "nfl": "🏈", "nba": "🏀", "nhl": "🏒",
    "wnba": "🏀", "mls": "⚽", "premier_league": "⚽",
}


def get_scores(sports_config: dict, timezone_str: str = "America/Los_Angeles") -> list:
    """Returns list of {"emoji", "text"} covering yesterday's finals and today's games."""
    try:
        local_tz = pytz.timezone(timezone_str)
    except Exception:
        local_tz = pytz.utc

    now_local = datetime.now(local_tz)
    today_str = now_local.strftime("%Y%m%d")
    yesterday_str = (now_local - timedelta(days=1)).strftime("%Y%m%d")

    results = []
    for league, teams in sports_config.items():
        if not teams:
            continue
        endpoint = ENDPOINTS.get(league)
        if not endpoint:
            continue

        yesterday_events = _fetch_events(endpoint, yesterday_str)
        today_events = _fetch_events(endpoint, today_str)

        for event in yesterday_events:
            row = _format_event(event, teams, local_tz, label="Yesterday")
            if row:
                results.append({"emoji": SPORT_EMOJIS.get(league, "🏆"), "text": row})

        for event in today_events:
            row = _format_event(event, teams, local_tz, label=None)
            if row:
                results.append({"emoji": SPORT_EMOJIS.get(league, "🏆"), "text": row})

    return results


def _fetch_events(endpoint: str, date_str: str) -> list:
    try:
        resp = requests.get(endpoint, params={"dates": date_str}, timeout=10)
        resp.raise_for_status()
        return resp.json().get("events", [])
    except Exception:
        logging.warning("Sports fetch failed for %s on %s", endpoint, date_str)
        return []


def _format_event(event: dict, teams: list, local_tz, label: str | None) -> str | None:
    competition = event.get("competitions", [{}])[0]
    competitors = competition.get("competitors", [])

    abbrevs = {c["team"].get("abbreviation", "").upper() for c in competitors if "team" in c}
    names = {c["team"].get("name", "").lower() for c in competitors if "team" in c}

    if not any(t.upper() in abbrevs or t.lower() in names for t in teams):
        return None

    completed = event.get("status", {}).get("type", {}).get("completed", False)

    if completed:
        home = next((c for c in competitors if c.get("homeAway") == "home"), None)
        away = next((c for c in competitors if c.get("homeAway") == "away"), None)
        if home and away:
            score = (
                f"{away['team']['name']} {away['score']}, "
                f"{home['team']['name']} {home['score']}  Final"
            )
        else:
            score = event.get("name", "") + "  Final"
        return f"{label}: {score}" if label else score
    else:
        event_date = event.get("date", "")
        if event_date:
            dt_utc = datetime.fromisoformat(event_date.replace("Z", "+00:00"))
            dt_local = dt_utc.astimezone(local_tz)
            time_str = dt_local.strftime("%I:%M %p").lstrip("0") or "12:00 AM"
            return f"{event['name']}  {time_str}"
        return event.get("name", "") or None
