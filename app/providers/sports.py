import requests
import logging
import pytz
from datetime import datetime, timezone

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


def get_scores(sports_config: dict, timezone_str: str = "America/Los_Angeles") -> list:
    """Returns list of {"emoji", "text"} for configured teams."""
    try:
        local_tz = pytz.timezone(timezone_str)
    except Exception:
        local_tz = pytz.utc
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
            logging.warning("Sports fetch failed for %s", league)
            continue

        for event in data.get("events", []):
            competition = event.get("competitions", [{}])[0]
            competitors = competition.get("competitors", [])

            abbrevs = {c["team"].get("abbreviation", "").upper() for c in competitors if "team" in c}
            names = {c["team"].get("name", "").lower() for c in competitors if "team" in c}

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
                    dt_utc = datetime.fromisoformat(event_date.replace("Z", "+00:00"))
                    dt_local = dt_utc.astimezone(local_tz)
                    time_str = dt_local.strftime("%I:%M %p").lstrip("0") or "12:00 AM"
                    text = f"{event['name']}  {time_str}"
                else:
                    text = event.get("name", "")

            results.append({"emoji": SPORT_EMOJIS.get(league, "🏆"), "text": text})

    return results
