from __future__ import annotations

import re

from thefuzz import fuzz

from pickem.models import Game, PlayerPicks
from pickem.scores import TEAM_ALIASES

# Regex to parse headers like "Jets (+12.5) @ Patriots [TNF]"
# Captures: away_team, spread_sign, spread_value, home_team, optional_tag
HEADER_RE = re.compile(
    r"^(.+?)\s*\(([+-]?\d+\.?\d*)\)\s*@\s*(.+?)(?:\s*\[(\w+)\])?\s*$"
)

# Columns to skip when looking for game picks
SKIP_COLUMNS = {"timestamp", "email address", "name", "ats bonus", "season performance"}


def parse_game_header(header: str) -> Game | None:
    """Parse a column header into a Game object.

    Expected format: "Jets (+12.5) @ Patriots [TNF]"
    The spread is always on the away team in the header. A positive spread means
    the away team is the underdog, negative means they're favored.
    """
    match = HEADER_RE.match(header.strip())
    if not match:
        return None

    away_team = match.group(1).strip()
    spread_val = float(match.group(2))
    home_team = match.group(3).strip()
    tag = match.group(4)

    # The spread in the header is on the away team
    # e.g., "Jets (+12.5)" means Jets are +12.5 underdogs
    spread_team = away_team

    return Game(
        away_team=away_team,
        home_team=home_team,
        spread=spread_val,
        spread_team=spread_team,
        column_header=header.strip(),
        tag=tag,
    )


def parse_responses(
    headers: list[str], rows: list[list[str]]
) -> tuple[list[Game], list[PlayerPicks]]:
    """Parse spreadsheet data into games and player picks.

    Returns (games, player_picks).
    """
    # Find game columns and non-game columns
    game_columns: list[tuple[int, Game]] = []
    name_col: int | None = None
    email_col: int | None = None
    ats_col: int | None = None

    for i, header in enumerate(headers):
        h_lower = header.strip().lower()
        if h_lower == "name":
            name_col = i
        elif h_lower == "email address":
            email_col = i
        elif h_lower == "ats bonus":
            ats_col = i
        elif h_lower not in SKIP_COLUMNS:
            game = parse_game_header(header)
            if game:
                game_columns.append((i, game))

    if name_col is None:
        raise ValueError("Could not find 'Name' column in headers")

    games = [g for _, g in game_columns]

    # Parse each row into PlayerPicks
    # Rows are sorted by timestamp (earliest first), so later rows override earlier
    # ones for the same email (handles duplicate submissions).
    players_by_email: dict[str, PlayerPicks] = {}
    for row in rows:
        if not row or len(row) <= (name_col or 0):
            continue
        name = row[name_col].strip() if name_col is not None else ""
        if not name:
            continue
        email = row[email_col].strip() if email_col is not None and email_col < len(row) else ""

        picks: dict[str, str] = {}
        for col_idx, game in game_columns:
            if col_idx < len(row):
                picks[game.column_header] = row[col_idx].strip()

        ats_team = None
        if ats_col is not None and ats_col < len(row):
            ats_team = row[ats_col].strip() or None

        player = PlayerPicks(name=name, email=email, picks=picks, ats_bonus_team=ats_team)
        # Use email as key to deduplicate — last submission wins
        key = email.lower() if email else name.lower()
        players_by_email[key] = player

    players = list(players_by_email.values())

    return games, players


def _resolve_alias(text: str) -> str | None:
    """If text matches a known alias, return the ESPN full team name."""
    return TEAM_ALIASES.get(text.strip().lower())


def _team_match_score(ats_text: str, team_name: str) -> int:
    """Score how well ats_text matches a team name, checking aliases first."""
    text_lower = ats_text.strip().lower()

    # Check if the text is a known alias that maps to a full ESPN name
    alias_resolved = _resolve_alias(text_lower)
    if alias_resolved:
        # Check if this alias maps to a team in this game
        if alias_resolved.lower() == team_name.lower():
            return 100
        # Also check if the alias partial-matches the short form name
        if fuzz.partial_ratio(alias_resolved.lower(), team_name.lower()) > 90:
            return 100

    # Also check aliases for substrings (e.g., "the fins" should match "fins")
    for alias, full_name in TEAM_ALIASES.items():
        if alias in text_lower and full_name.lower() == team_name.lower():
            return 95

    # Fall back to fuzzy matching
    return max(
        fuzz.partial_ratio(text_lower, team_name.lower()),
        fuzz.token_sort_ratio(text_lower, team_name.lower()),
    )


def match_ats_team(
    ats_text: str, games: list[Game], threshold: int = 60
) -> Game | None:
    """Fuzzy-match the ATS bonus text to a team in one of the games.

    Returns the Game that the player's ATS pick corresponds to, or None.
    """
    if not ats_text:
        return None

    best_score = 0
    best_game: Game | None = None

    for game in games:
        for team in (game.away_team, game.home_team):
            score = _team_match_score(ats_text, team)
            if score > best_score:
                best_score = score
                best_game = game

    if best_score >= threshold:
        return best_game
    return None


def identify_ats_pick_team(ats_text: str, game: Game) -> str:
    """Given the ATS text and matched game, figure out which team they picked."""
    away_score = _team_match_score(ats_text, game.away_team)
    home_score = _team_match_score(ats_text, game.home_team)
    return game.away_team if away_score >= home_score else game.home_team
