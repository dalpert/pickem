from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Game:
    """A single NFL matchup parsed from a form column header.

    The spread is always relative to the away team as shown in the header.
    e.g., "Jets (+12.5) @ Patriots" means Jets are +12.5 (underdogs).
    """

    away_team: str
    home_team: str
    spread: float  # Spread on the away team. Positive = away is underdog.
    spread_team: str  # Always the away team (who the spread is listed on)
    column_header: str  # Original header text for reference
    tag: str | None = None  # e.g. "TNF", "MNF"


@dataclass
class GameResult:
    """Actual final score for an NFL game."""

    home_team: str
    away_team: str
    home_score: int
    away_score: int

    @property
    def winner(self) -> str | None:
        if self.home_score > self.away_score:
            return self.home_team
        elif self.away_score > self.home_score:
            return self.away_team
        return None  # Tie

    @property
    def margin(self) -> int:
        """Positive = home team won by this much, negative = away team won."""
        return self.home_score - self.away_score


@dataclass
class PlayerPicks:
    """One player's picks for the week."""

    name: str
    email: str
    picks: dict[str, str]  # column_header -> team they picked
    ats_bonus_team: str | None  # Team name they entered for ATS bonus


@dataclass
class PlayerResult:
    """Graded result for one player."""

    name: str
    correct: int
    total: int
    pushes: int
    ats_bonus_score: float | None  # Their ATS bonus value
    ats_bonus_team: str | None
    details: list[PickDetail] = field(default_factory=list)

    @property
    def losses(self) -> int:
        return self.total - self.correct - self.pushes

    @property
    def pct(self) -> float:
        decided = self.total - self.pushes
        return self.correct / decided if decided > 0 else 0.0


@dataclass
class PickDetail:
    """Detail for a single pick showing what happened."""

    game: Game
    picked: str
    picked_away: bool  # True if they picked the away team
    actual_winner: str | None  # Straight-up winner
    correct: bool  # Covered the spread
    push: bool  # Exactly hit the spread
    home_score: int
    away_score: int
    ats_margin: float  # How much the picked team covered by (positive = covered)
