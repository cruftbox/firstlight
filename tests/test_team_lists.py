"""Guards the setup wizard's team picker against ESPN roster drift.

The picker writes a team's ESPN **id** into config, and the sports provider
resolves configured labels to ids before matching events. Ids are stable across
rebrands, so this is much harder to break than the old abbreviation matching —
but the picker's list is still a snapshot, and a team that leaves a league or an
id that is retired would go stale silently. Nothing else in the suite notices,
because the failure has no error path.

Abbreviations are still checked: they remain the search/display labels, and the
provider falls back to matching on them when the roster is unreachable.

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

ENTRY = re.compile(r'\{id:"([^"]*)",abbr:"([^"]*)",name:"([^"]*)"\}')


def _picker_teams(league: str) -> list:
    """[{id, abbr, name}] for one league, parsed out of the autocomplete source."""
    js = JS_PATH.read_text(encoding="utf-8")
    # Anchor to line start: an unanchored "nba" also matches inside "wnba".
    block = re.search(r"^\s*" + league + r"\s*:\s*\[(.*?)\]", js, re.S | re.M)
    assert block, f"league {league!r} missing from {JS_PATH.name}"
    teams = [{"id": i, "abbr": a, "name": n} for i, a, n in ENTRY.findall(block.group(1))]
    assert teams, f"league {league!r} parsed as empty — has the entry format changed?"
    return teams


def _espn_teams(path: str) -> dict:
    """{id: displayName} for one league, from ESPN. Skips if unreachable."""
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

    return {str(t["team"]["id"]): t["team"]["displayName"] for t in teams}


@pytest.mark.network
@pytest.mark.parametrize("league", sorted(LEAGUE_PATHS))
def test_no_dead_team_ids(league):
    """Every id the picker can write must still exist at ESPN.

    This is the load-bearing check: the id is what ends up in config and what
    events are matched on.
    """
    picker = _picker_teams(league)
    live = _espn_teams(LEAGUE_PATHS[league])

    dead = [t for t in picker if t["id"] not in live]
    assert not dead, (
        f"{league}: {len(dead)} team id(s) no longer exist at ESPN — anyone who "
        "selected these gets no scores: "
        + ", ".join(f"{t['name']} (id {t['id']})" for t in dead)
    )


@pytest.mark.network
@pytest.mark.parametrize("league", sorted(LEAGUE_PATHS))
def test_abbreviations_still_current(league):
    """Abbreviations drive search and the roster-outage fallback path.

    Less severe than a dead id, but a stale one degrades both.
    """
    picker = _picker_teams(league)
    live_abbrevs = set()
    url = f"https://site.api.espn.com/apis/site/v2/sports/{LEAGUE_PATHS[league]}/teams"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.load(resp)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        pytest.skip(f"ESPN unreachable for {LEAGUE_PATHS[league]}: {exc}")
    for entry in data["sports"][0]["leagues"][0]["teams"]:
        live_abbrevs.add(entry["team"]["abbreviation"])

    stale = [t for t in picker if t["abbr"] not in live_abbrevs]
    assert not stale, (
        f"{league}: {len(stale)} abbreviation(s) are out of date: "
        + ", ".join(f"{t['abbr']} ({t['name']})" for t in stale)
    )


@pytest.mark.network
@pytest.mark.parametrize("league", sorted(LEAGUE_PATHS))
def test_no_missing_teams(league):
    """The picker should offer every team in the league.

    Nothing breaks when one is absent — it just can't be chosen — but this is
    how expansion and promotion drift in.
    """
    picker_ids = {t["id"] for t in _picker_teams(league)}
    live = _espn_teams(LEAGUE_PATHS[league])

    missing = {i: n for i, n in live.items() if i not in picker_ids}
    assert not missing, (
        f"{league}: {len(missing)} team(s) at ESPN are absent from the picker: "
        + ", ".join(f"{n} (id {i})" for i, n in sorted(missing.items()))
    )


@pytest.mark.network
def test_every_configured_league_is_audited():
    """A league added to the provider must also be covered here."""
    from app.providers.sports import ENDPOINTS
    assert set(ENDPOINTS) == set(LEAGUE_PATHS), (
        "LEAGUE_PATHS is out of sync with app/providers/sports.py ENDPOINTS: "
        f"{set(ENDPOINTS) ^ set(LEAGUE_PATHS)}"
    )
