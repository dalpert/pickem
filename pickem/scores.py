from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import httpx
from thefuzz import fuzz

from pickem.models import GameResult

ESPN_SCOREBOARD_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
)

CACHE_DIR = Path.home() / ".cache" / "pickem"

# Map common short/informal/joke names to ESPN's display names
TEAM_ALIASES: dict[str, str] = {
    # Arizona Cardinals
    "cards": "Arizona Cardinals",
    "cardinals": "Arizona Cardinals",
    # Atlanta Falcons
    "falcons": "Atlanta Falcons",
    "dirty birds": "Atlanta Falcons",
    # Baltimore Ravens
    "ravens": "Baltimore Ravens",
    # Buffalo Bills
    "bills": "Buffalo Bills",
    "buff": "Buffalo Bills",
    # Carolina Panthers
    "panthers": "Carolina Panthers",
    # Chicago Bears
    "bears": "Chicago Bears",
    "da bears": "Chicago Bears",
    # Cincinnati Bengals
    "bengals": "Cincinnati Bengals",
    "bungles": "Cincinnati Bengals",
    # Cleveland Browns
    "browns": "Cleveland Browns",
    # Dallas Cowboys
    "cowboys": "Dallas Cowboys",
    "boys": "Dallas Cowboys",
    "cows": "Dallas Cowboys",
    # Denver Broncos
    "broncos": "Denver Broncos",
    # Detroit Lions
    "lions": "Detroit Lions",
    # Green Bay Packers
    "packers": "Green Bay Packers",
    "pack": "Green Bay Packers",
    # Houston Texans
    "texans": "Houston Texans",
    # Indianapolis Colts
    "colts": "Indianapolis Colts",
    # Jacksonville Jaguars
    "jaguars": "Jacksonville Jaguars",
    "jags": "Jacksonville Jaguars",
    # Kansas City Chiefs
    "chiefs": "Kansas City Chiefs",
    "chefs": "Kansas City Chiefs",
    "kc": "Kansas City Chiefs",
    # Las Vegas Raiders
    "raiders": "Las Vegas Raiders",
    # Los Angeles Chargers
    "chargers": "Los Angeles Chargers",
    "bolts": "Los Angeles Chargers",
    # Los Angeles Rams
    "rams": "Los Angeles Rams",
    # Miami Dolphins
    "dolphins": "Miami Dolphins",
    "fins": "Miami Dolphins",
    "phins": "Miami Dolphins",
    # Minnesota Vikings
    "vikings": "Minnesota Vikings",
    "vikes": "Minnesota Vikings",
    # New England Patriots
    "patriots": "New England Patriots",
    "pats": "New England Patriots",
    # New Orleans Saints
    "saints": "New Orleans Saints",
    # New York Giants
    "giants": "New York Giants",
    "gmen": "New York Giants",
    "g-men": "New York Giants",
    # New York Jets
    "jets": "New York Jets",
    # Philadelphia Eagles
    "eagles": "Philadelphia Eagles",
    "birds": "Philadelphia Eagles",
    "iggles": "Philadelphia Eagles",
    # Pittsburgh Steelers
    "steelers": "Pittsburgh Steelers",
    # San Francisco 49ers
    "49ers": "San Francisco 49ers",
    "niners": "San Francisco 49ers",
    "9ers": "San Francisco 49ers",
    "sf": "San Francisco 49ers",
    # Seattle Seahawks
    "seahawks": "Seattle Seahawks",
    "hawks": "Seattle Seahawks",
    # Tampa Bay Buccaneers
    "buccaneers": "Tampa Bay Buccaneers",
    "bucs": "Tampa Bay Buccaneers",
    # Tennessee Titans
    "titans": "Tennessee Titans",
    "tits": "Tennessee Titans",
    # Washington Commanders
    "commanders": "Washington Commanders",
    "commies": "Washington Commanders",
    "skins": "Washington Commanders",
    "nats": "Washington Commanders",
}


def current_nfl_season() -> int:
    """Determine the current NFL season year.

    NFL seasons span two calendar years. The season is identified by the year
    it starts in (e.g., the 2025-26 season is "2025"). If we're before September,
    we're still in the previous season.
    """
    now = datetime.now()
    if now.month < 3:
        return now.year - 1
    return now.year


def _cache_path(season: int, week: int) -> Path:
    return CACHE_DIR / f"scores_{season}_week{week}.json"


def _load_cache(season: int, week: int) -> list[GameResult] | None:
    path = _cache_path(season, week)
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return [GameResult(**g) for g in data]


def _save_cache(season: int, week: int, results: list[GameResult]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _cache_path(season, week)
    data = [
        {
            "home_team": r.home_team,
            "away_team": r.away_team,
            "home_score": r.home_score,
            "away_score": r.away_score,
        }
        for r in results
    ]
    path.write_text(json.dumps(data, indent=2))


def fetch_scores(season: int, week: int, *, use_cache: bool = True) -> list[GameResult]:
    """Fetch NFL scores for a given week from ESPN's API.

    Returns a list of GameResult objects for all completed games.
    """
    if use_cache:
        cached = _load_cache(season, week)
        if cached:
            return cached

    resp = httpx.get(
        ESPN_SCOREBOARD_URL,
        params={"dates": season, "seasontype": 2, "week": week},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    results: list[GameResult] = []
    for event in data.get("events", []):
        competition = event["competitions"][0]
        status = competition["status"]["type"]

        if not status.get("completed", False):
            continue

        competitors = competition["competitors"]
        home = next(c for c in competitors if c["homeAway"] == "home")
        away = next(c for c in competitors if c["homeAway"] == "away")

        results.append(
            GameResult(
                home_team=home["team"]["displayName"],
                away_team=away["team"]["displayName"],
                home_score=int(home["score"]),
                away_score=int(away["score"]),
            )
        )

    if results and use_cache:
        _save_cache(season, week, results)

    return results


def _team_score(form_team: str, espn_team: str) -> int:
    """Score how well a form team name matches an ESPN team name."""
    alias_match = TEAM_ALIASES.get(form_team.lower())
    if alias_match:
        if alias_match.lower() == espn_team.lower():
            return 100

    return max(
        fuzz.partial_ratio(form_team.lower(), espn_team.lower()),
        fuzz.token_sort_ratio(form_team.lower(), espn_team.lower()),
    )


def match_game_result(
    away_team: str, home_team: str, results: list[GameResult], threshold: int = 70
) -> GameResult | None:
    """Find the GameResult matching the given team names using fuzzy matching.

    Tries both orientations (away/home and home/away) since forms sometimes
    have the home/away swapped from what ESPN reports.

    IMPORTANT: Returns the result normalized so that result.away_team corresponds
    to the form's away_team and result.home_team corresponds to the form's home_team.
    This ensures the grader can safely use result.away_score + game.spread.
    """
    best_result: GameResult | None = None
    best_score = 0
    best_flipped = False

    for result in results:
        # Try normal orientation: form_away=espn_away, form_home=espn_home
        normal = (
            _team_score(away_team, result.away_team)
            + _team_score(home_team, result.home_team)
        ) / 2

        # Try flipped: form_away=espn_home, form_home=espn_away
        flipped = (
            _team_score(away_team, result.home_team)
            + _team_score(home_team, result.away_team)
        ) / 2

        if normal >= flipped and normal > best_score:
            best_score = normal
            best_result = result
            best_flipped = False
        elif flipped > normal and flipped > best_score:
            best_score = flipped
            best_result = result
            best_flipped = True

    if best_score >= threshold and best_result is not None:
        if best_flipped:
            # Return a new GameResult with swapped home/away to match the form
            return GameResult(
                home_team=best_result.away_team,
                away_team=best_result.home_team,
                home_score=best_result.away_score,
                away_score=best_result.home_score,
            )
        return best_result
    return None
