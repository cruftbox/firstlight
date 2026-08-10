import requests
import logging
from app.providers.utils import get_with_retry
import pytz
from datetime import datetime, timezone, timedelta

ENDPOINTS = {
    "mlb": "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard",
    "nfl": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
    "nba": "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
    "nhl": "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard",
    "wnba": "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard",
    "nwsl": "https://site.api.espn.com/apis/site/v2/sports/soccer/usa.nwsl/scoreboard",
    "mls": "https://site.api.espn.com/apis/site/v2/sports/soccer/usa.1/scoreboard",
    "premier_league": "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard",
}

WORLD_CUP_ENDPOINT = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"

SPORT_EMOJIS = {
    "mlb": "⚾", "nfl": "🏈", "nba": "🏀", "nhl": "🏒",
    "wnba": "🏀", "nwsl": "⚽", "mls": "⚽", "premier_league": "⚽",
}


def get_scores(sports_config: dict, timezone_str: str = "America/Los_Angeles",
               warnings: list | None = None) -> list:
    """Returns list of {"emoji", "text"} covering yesterday's finals and today's games.

    If `warnings` is given, appends a one-line notice for any configured team
    whose name is not in the league's roster — almost always a stale or
    mistyped abbreviation, which otherwise fails silently.
    """
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

        if warnings is not None:
            _warn_unknown_teams(league, endpoint, teams, warnings)

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


def _fetch_roster(endpoint: str) -> tuple[set, set] | None:
    """Return (abbreviations upper, names lower) for a league, or None if unavailable.

    Mirrors the two ways _format_event matches a configured team.
    """
    try:
        resp = get_with_retry(endpoint.replace("/scoreboard", "/teams"), timeout=10)
        teams = resp.json()["sports"][0]["leagues"][0]["teams"]
    except Exception as e:
        logging.warning("Roster fetch failed for %s: %s", endpoint, e)
        return None

    abbrevs, names = set(), set()
    for entry in teams:
        team = entry.get("team", {})
        if team.get("abbreviation"):
            abbrevs.add(team["abbreviation"].upper())
        if team.get("name"):
            names.add(team["name"].lower())
    return (abbrevs, names) if abbrevs else None


def _warn_unknown_teams(league: str, endpoint: str, teams: list, warnings: list) -> None:
    """Append a notice for configured teams the league does not recognize.

    Fails open: if the roster cannot be fetched we say nothing rather than
    warning about teams we were simply unable to verify.
    """
    roster = _fetch_roster(endpoint)
    if roster is None:
        return
    abbrevs, names = roster

    unknown = [t for t in teams if t.upper() not in abbrevs and t.lower() not in names]
    for team in unknown:
        logging.warning("Configured %s team %r is not in the league roster", league, team)
        warnings.append(f"{league.upper()} team “{team}” not recognized")


def _fetch_events(endpoint: str, date_str: str) -> list:
    try:
        resp = get_with_retry(endpoint, params={"dates": date_str}, timeout=10)
        return resp.json().get("events", [])
    except Exception as e:
        logging.warning("Sports fetch failed for %s on %s: %s", endpoint, date_str, e)
        return []


def get_world_cup(timezone_str: str = "America/Los_Angeles") -> list:
    """Returns World Cup matches for yesterday (scores), today, and tomorrow (kickoffs).
    Returns empty list if no matches exist or endpoint is unavailable."""
    try:
        local_tz = pytz.timezone(timezone_str)
    except Exception:
        local_tz = pytz.utc

    now = datetime.now(local_tz)
    dates = {
        "Yesterday": (now - timedelta(days=1)).strftime("%Y%m%d"),
        "Today":     now.strftime("%Y%m%d"),
        "Tomorrow":  (now + timedelta(days=1)).strftime("%Y%m%d"),
    }

    results = []
    for label, date_str in dates.items():
        events = _fetch_events(WORLD_CUP_ENDPOINT, date_str)
        for event in events:
            row = _format_wc_event(event, local_tz, label)
            if row:
                results.append(row)
    return results


def _format_wc_event(event: dict, local_tz, label: str) -> dict | None:
    competition = event.get("competitions", [{}])[0]
    competitors = competition.get("competitors", [])
    if len(competitors) < 2:
        return None

    home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
    away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])
    home_name = home.get("team", {}).get("displayName") or home.get("team", {}).get("name", "?")
    away_name = away.get("team", {}).get("displayName") or away.get("team", {}).get("name", "?")

    status = event.get("status", {}).get("type", {})
    completed = status.get("completed", False)
    in_progress = not completed and status.get("state", "") == "in"

    if completed:
        text = f"{away_name} {away.get('score', '?')} – {home.get('score', '?')} {home_name}  Final"
    elif in_progress:
        clock = event.get("status", {}).get("displayClock", "")
        period = event.get("status", {}).get("period", "")
        period_str = f" ({period}')" if period else (f" ({clock})" if clock else "")
        text = f"{away_name} {away.get('score', '0')} – {home.get('score', '0')} {home_name}{period_str}"
    else:
        event_date = event.get("date", "")
        if event_date:
            dt_utc = datetime.fromisoformat(event_date.replace("Z", "+00:00"))
            dt_local = dt_utc.astimezone(local_tz)
            time_str = dt_local.strftime("%I:%M %p").lstrip("0") or "12:00 AM"
            text = f"{away_name} vs {home_name}  {time_str}"
        else:
            text = f"{away_name} vs {home_name}"

    round_name = competition.get("notes", [{}])[0].get("headline", "") if competition.get("notes") else ""

    return {"label": label, "text": text, "round": round_name}


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
