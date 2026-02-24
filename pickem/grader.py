from __future__ import annotations

from thefuzz import fuzz

from pickem.models import Game, GameResult, PickDetail, PlayerPicks, PlayerResult
from pickem.parser import identify_ats_pick_team, match_ats_team
from pickem.scores import TEAM_ALIASES, match_game_result


def _identify_picked_side(picked: str, game: Game, result: GameResult) -> bool:
    """Determine if the player picked the away team (True) or home team (False).

    We match their pick text against both teams and choose the better match.
    """
    def score(text: str, team: str) -> int:
        alias = TEAM_ALIASES.get(text.strip().lower())
        if alias and alias.lower() == team.lower():
            return 100
        return max(
            fuzz.partial_ratio(text.lower(), team.lower()),
            fuzz.token_sort_ratio(text.lower(), team.lower()),
        )

    # Match against both the form short names and ESPN full names
    away_score = max(score(picked, game.away_team), score(picked, result.away_team))
    home_score = max(score(picked, game.home_team), score(picked, result.home_team))

    return away_score >= home_score  # True = picked away


def _grade_pick_ats(
    picked_away: bool, game: Game, result: GameResult
) -> tuple[bool, bool, float]:
    """Grade a pick against the spread.

    The spread is always on the away team in the header:
      "Patriots (+10) @ Bills" means Patriots get +10 points.

    To evaluate: adjusted_away_score = away_score + spread
    If adjusted_away > home_score: away covers -> picking away wins
    If adjusted_away < home_score: home covers -> picking home wins
    If adjusted_away == home_score: PUSH

    Returns (correct, push, ats_margin).
    ats_margin = how much the picked side covered by (positive = covered).
    """
    adjusted_away = result.away_score + game.spread

    if adjusted_away > result.home_score:
        # Away team covered the spread
        away_covered = True
        push = False
    elif adjusted_away < result.home_score:
        # Home team covered
        away_covered = False
        push = False
    else:
        # Push — exactly on the spread
        away_covered = False
        push = True

    if push:
        correct = False
        ats_margin = 0.0
    elif picked_away:
        correct = away_covered
        ats_margin = adjusted_away - result.home_score
    else:
        correct = not away_covered
        ats_margin = result.home_score - adjusted_away

    return correct, push, ats_margin


def compute_ats_bonus(
    ats_team: str | None, games: list[Game], results: list[GameResult]
) -> tuple[float | None, str | None]:
    """Compute the ATS bonus score for a player's ATS pick.

    The ATS bonus = how much the team they picked covered (or didn't cover)
    the spread by. Uses the same spread logic as the main grading.

    Returns (ats_score, resolved_team_name) or (None, None) if we can't resolve.
    """
    if not ats_team:
        return None, None

    game = match_ats_team(ats_team, games)
    if game is None:
        return None, None

    picked_team = identify_ats_pick_team(ats_team, game)

    result = match_game_result(game.away_team, game.home_team, results)
    if result is None:
        return None, picked_team

    # Determine if they picked the away team
    picked_away = _is_away_team(picked_team, game)

    # Calculate ATS margin from their perspective
    adjusted_away = result.away_score + game.spread
    if picked_away:
        ats_score = adjusted_away - result.home_score
    else:
        ats_score = result.home_score - adjusted_away

    return ats_score, picked_team


def _is_away_team(team_name: str, game: Game) -> bool:
    """Check if team_name refers to the away team in the game."""
    away_score = max(
        fuzz.partial_ratio(team_name.lower(), game.away_team.lower()),
        fuzz.token_sort_ratio(team_name.lower(), game.away_team.lower()),
    )
    home_score = max(
        fuzz.partial_ratio(team_name.lower(), game.home_team.lower()),
        fuzz.token_sort_ratio(team_name.lower(), game.home_team.lower()),
    )
    return away_score >= home_score


def grade_picks(
    games: list[Game],
    players: list[PlayerPicks],
    results: list[GameResult],
) -> list[PlayerResult]:
    """Grade all players' picks against the spread.

    Returns a list of PlayerResult sorted by correct picks (desc), then ATS bonus (desc).
    """
    player_results: list[PlayerResult] = []

    for player in players:
        correct = 0
        pushes = 0
        total = 0
        details: list[PickDetail] = []

        for game in games:
            picked = player.picks.get(game.column_header, "")
            if not picked:
                continue

            result = match_game_result(game.away_team, game.home_team, results)
            if result is None:
                continue

            total += 1
            picked_away = _identify_picked_side(picked, game, result)
            is_correct, is_push, ats_margin = _grade_pick_ats(picked_away, game, result)

            if is_correct:
                correct += 1
            if is_push:
                pushes += 1

            details.append(
                PickDetail(
                    game=game,
                    picked=picked,
                    picked_away=picked_away,
                    actual_winner=result.winner,
                    correct=is_correct,
                    push=is_push,
                    home_score=result.home_score,
                    away_score=result.away_score,
                    ats_margin=ats_margin,
                )
            )

        ats_score, ats_resolved = compute_ats_bonus(
            player.ats_bonus_team, games, results
        )

        player_results.append(
            PlayerResult(
                name=player.name,
                correct=correct,
                total=total,
                pushes=pushes,
                ats_bonus_score=ats_score,
                ats_bonus_team=ats_resolved,
                details=details,
            )
        )

    # Sort: most correct first, then highest ATS bonus
    player_results.sort(
        key=lambda r: (r.correct, r.ats_bonus_score or float("-inf")),
        reverse=True,
    )

    return player_results
