"""Guards the setup wizard's team picker against ESPN roster drift.

The picker writes a team's *abbreviation* into config, and the sports provider
matches on that abbreviation exactly. When ESPN renames a team or a league
changes membership, a stale entry keeps looking valid in the UI while silently
matching nothing — the digest just prints less. Nothing else in the suite
notices, because the failure has no error path.

These tests hit live ESPN endpoints, so they are marked `network` and excluded
from the default run (see pytest.ini). Run them with:

    pytest -m network

They run monthly in CI via .github/workflows/team-lists.yml.
"""
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

import pytest

JS_PATH = Path(__file__).resolve().parent.parent / "app" / "static" / "js" / "sports-autocomplete.js"

# league key -> ESPN path segment, mirroring ENDPOINTS in app/providers/sports.py
LEAGUE_PATHS = {
    "mlb": "baseball/mlb",
    "nfl": "football/nfl",
    "nba": "basketball/nba",
    "nhl": "hockey/nhl",
    "wnba": "basketball/wnba",
    "nwsl": "soccer/usa.nwsl",
    "mls": "soccer/usa.1",
    "premier_league": "soccer/eng.1",
}


def _picker_teams(league: str) -> dict:
    """{abbr: name} for one league, parsed out of the autocomplete source."""
    js = JS_PATH.read_text(encoding="utf-8")
    block = re.search(league + r"\s*:\s*\[(.*?)\]", js, re.S)
    assert block, f"league {league!r} missing from {JS_PATH.name}"
    return dict(re.findall(r'\{abbr:"([^"]*)",name:"([^"]*)"\}', block.group(1)))


def _espn_teams(path: str) -> dict:
    """{abbr: displayName} for one league, from ESPN. Skips if unreachable."""
    url = f"https://site.api.espn.com/apis/site/v2/sports/{path}/teams"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.load(resp)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        pytest.skip(f"ESPN unreachable for {path}: {exc}")

    try:
        teams = data["sports"][0]["leagues"][0]["teams"]
    except (KeyError, IndexError):
        pytest.skip(f"Unexpected ESPN payload shape for {path}")

    return {t["team"]["abbreviation"]: t["team"]["displayName"] for t in teams}


@pytest.mark.network
@pytest.mark.parametrize("league", sorted(LEAGUE_PATHS))
def test_no_dead_abbreviations(league):
    """Every abbreviation the picker can write must still exist at ESPN.

    A failure here means anyone who picked that team is silently getting no
    scores for it.
    """
    picker = _picker_teams(league)
    live = _espn_teams(LEAGUE_PATHS[league])

    dead = {a: n for a, n in picker.items() if a not in live}
    assert not dead, (
        f"{league}: {len(dead)} abbreviation(s) no longer exist at ESPN — anyone who "
        f"selected these gets no scores: "
        + ", ".join(f"{a} ({n})" for a, n in sorted(dead.items()))
        + f"\nCurrent ESPN roster: "
        + ", ".join(f"{a}={n}" for a, n in sorted(live.items()))
    )


@pytest.mark.network
@pytest.mark.parametrize("league", sorted(LEAGUE_PATHS))
def test_no_missing_teams(league):
    """The picker should offer every team in the league.

    Less severe than a dead abbreviation — nothing breaks, the team just can't
    be chosen — but it is how expansion and promotion drift in.
    """
    picker = _picker_teams(league)
    live = _espn_teams(LEAGUE_PATHS[league])

    missing = {a: n for a, n in live.items() if a not in picker}
    assert not missing, (
        f"{league}: {len(missing)} team(s) at ESPN are absent from the picker: "
        + ", ".join(f"{a} ({n})" for a, n in sorted(missing.items()))
    )


@pytest.mark.network
def test_every_configured_league_is_audited():
    """A league added to the provider must also be covered here."""
    from app.providers.sports import ENDPOINTS
    assert set(ENDPOINTS) == set(LEAGUE_PATHS), (
        "LEAGUE_PATHS is out of sync with app/providers/sports.py ENDPOINTS: "
        f"{set(ENDPOINTS) ^ set(LEAGUE_PATHS)}"
    )
