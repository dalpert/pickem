from __future__ import annotations

from dataclasses import dataclass, field

import click
from tabulate import tabulate

from pickem.models import Game, PlayerResult
from pickem.names import canonical_name


@dataclass
class PlayerSeason:
    """Aggregated season stats for one player."""

    name: str
    weeks_played: int = 0
    total_correct: int = 0
    total_games: int = 0
    total_pushes: int = 0
    total_ats_bonus: float = 0.0
    weekly_records: dict[int, tuple[int, int, int]] = field(default_factory=dict)  # week -> (W, L, P)
    weekly_ats: dict[int, float | None] = field(default_factory=dict)  # week -> ATS score

    @property
    def total_losses(self) -> int:
        return self.total_games - self.total_correct - self.total_pushes

    @property
    def win_pct(self) -> float:
        decided = self.total_games - self.total_pushes
        return self.total_correct / decided if decided > 0 else 0.0


@dataclass
class SeasonData:
    """Full season aggregation."""

    players: dict[str, PlayerSeason]  # canonical name -> PlayerSeason
    weeks_graded: list[int]

    @property
    def standings(self) -> list[PlayerSeason]:
        """Players sorted by wins desc, then ATS bonus desc."""
        return sorted(
            self.players.values(),
            key=lambda p: (p.total_correct, p.total_ats_bonus),
            reverse=True,
        )


def aggregate_season(
    all_week_results: dict[int, tuple[list[Game], list[PlayerResult]]],
) -> SeasonData:
    """Aggregate weekly results into season totals."""
    players: dict[str, PlayerSeason] = {}
    weeks_graded = sorted(all_week_results.keys())

    for week, (games, player_results) in all_week_results.items():
        for pr in player_results:
            name = pr.name
            if name not in players:
                players[name] = PlayerSeason(name=name)

            ps = players[name]
            ps.weeks_played += 1
            ps.total_correct += pr.correct
            ps.total_games += pr.total
            ps.total_pushes += pr.pushes
            ps.weekly_records[week] = (pr.correct, pr.losses, pr.pushes)

            if pr.ats_bonus_score is not None:
                ps.total_ats_bonus += pr.ats_bonus_score
                ps.weekly_ats[week] = pr.ats_bonus_score
            else:
                ps.weekly_ats[week] = None

    return SeasonData(players=players, weeks_graded=weeks_graded)


def print_season_summary(data: SeasonData) -> None:
    """Print a season summary to the terminal."""
    click.echo()
    click.echo("=" * 70)
    click.echo("  SEASON STANDINGS")
    click.echo("=" * 70)

    table = []
    for i, ps in enumerate(data.standings, 1):
        table.append([
            i,
            ps.name,
            ps.total_correct,
            ps.total_losses,
            ps.total_pushes,
            f"{ps.win_pct:.1%}",
            f"{ps.total_ats_bonus:+.1f}",
            ps.weeks_played,
        ])

    click.echo(tabulate(
        table,
        headers=["Rank", "Name", "W", "L", "P", "Pct", "ATS Total", "Weeks"],
        tablefmt="simple",
    ))

    # Week-by-week breakdown
    click.echo()
    click.echo("=" * 70)
    click.echo("  WEEK-BY-WEEK RECORDS")
    click.echo("=" * 70)

    standings = data.standings
    week_table = []
    for week in data.weeks_graded:
        row = [f"Week {week}"]
        for ps in standings:
            record = ps.weekly_records.get(week)
            if record:
                w, l, p = record
                rec_str = f"{w}-{l}"
                if p > 0:
                    rec_str += f"-{p}"
                row.append(rec_str)
            else:
                row.append("-")
        week_table.append(row)

    click.echo(tabulate(
        week_table,
        headers=[""] + [ps.name for ps in standings],
        tablefmt="simple",
    ))
