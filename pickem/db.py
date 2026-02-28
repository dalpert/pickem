"""SQLite database layer for persisting graded pick'em results."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from pickem.models import Game, PickDetail, PlayerResult


def init_db(db_path: str | Path) -> sqlite3.Connection:
    """Create tables if they don't exist and return a connection."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(_SCHEMA)
    return conn


_SCHEMA = """
CREATE TABLE IF NOT EXISTS seasons (
    id INTEGER PRIMARY KEY,
    label TEXT NOT NULL,
    sheet_id TEXT,
    weeks_available TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    email TEXT,
    avatar_filename TEXT
);

CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season_id INTEGER NOT NULL REFERENCES seasons(id),
    week INTEGER NOT NULL,
    away_team TEXT NOT NULL,
    home_team TEXT NOT NULL,
    spread REAL NOT NULL,
    tag TEXT,
    away_score INTEGER,
    home_score INTEGER,
    UNIQUE(season_id, week, away_team, home_team)
);

CREATE TABLE IF NOT EXISTS picks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season_id INTEGER NOT NULL REFERENCES seasons(id),
    week INTEGER NOT NULL,
    player_id INTEGER NOT NULL REFERENCES players(id),
    game_id INTEGER NOT NULL REFERENCES games(id),
    picked_team TEXT NOT NULL,
    picked_away INTEGER NOT NULL,
    correct INTEGER NOT NULL,
    push INTEGER NOT NULL DEFAULT 0,
    ats_margin REAL NOT NULL,
    UNIQUE(season_id, week, player_id, game_id)
);

CREATE TABLE IF NOT EXISTS weekly_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season_id INTEGER NOT NULL REFERENCES seasons(id),
    week INTEGER NOT NULL,
    player_id INTEGER NOT NULL REFERENCES players(id),
    correct INTEGER NOT NULL,
    total INTEGER NOT NULL,
    pushes INTEGER NOT NULL DEFAULT 0,
    ats_bonus_team TEXT,
    ats_bonus_score REAL,
    UNIQUE(season_id, week, player_id)
);

CREATE TABLE IF NOT EXISTS season_standings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season_id INTEGER NOT NULL REFERENCES seasons(id),
    player_id INTEGER NOT NULL REFERENCES players(id),
    weeks_played INTEGER NOT NULL,
    total_correct INTEGER NOT NULL,
    total_games INTEGER NOT NULL,
    total_pushes INTEGER NOT NULL DEFAULT 0,
    total_ats_bonus REAL NOT NULL DEFAULT 0.0,
    win_pct REAL NOT NULL,
    rank INTEGER,
    UNIQUE(season_id, player_id)
);

CREATE INDEX IF NOT EXISTS idx_picks_season_week ON picks(season_id, week);
CREATE INDEX IF NOT EXISTS idx_picks_player ON picks(player_id);
CREATE INDEX IF NOT EXISTS idx_weekly_results_season ON weekly_results(season_id, week);
CREATE INDEX IF NOT EXISTS idx_games_season_week ON games(season_id, week);
CREATE INDEX IF NOT EXISTS idx_season_standings_season ON season_standings(season_id);
"""


def upsert_season(
    conn: sqlite3.Connection,
    season_id: int,
    label: str,
    sheet_id: str | None = None,
) -> None:
    """Insert or update a season row."""
    conn.execute(
        """INSERT INTO seasons (id, label, sheet_id, weeks_available)
           VALUES (?, ?, ?, '[]')
           ON CONFLICT(id) DO UPDATE SET label=excluded.label, sheet_id=excluded.sheet_id""",
        (season_id, label, sheet_id),
    )
    conn.commit()


def upsert_player(
    conn: sqlite3.Connection,
    name: str,
    email: str | None = None,
    avatar_filename: str | None = None,
) -> int:
    """Insert or update a player, return their id."""
    conn.execute(
        """INSERT INTO players (name, email, avatar_filename)
           VALUES (?, ?, ?)
           ON CONFLICT(name) DO UPDATE SET
             email=COALESCE(excluded.email, players.email),
             avatar_filename=COALESCE(excluded.avatar_filename, players.avatar_filename)""",
        (name, email, avatar_filename),
    )
    conn.commit()
    row = conn.execute("SELECT id FROM players WHERE name = ?", (name,)).fetchone()
    return row[0]


def _get_or_create_player(conn: sqlite3.Connection, name: str) -> int:
    """Get player id by name, creating a minimal row if needed."""
    row = conn.execute("SELECT id FROM players WHERE name = ?", (name,)).fetchone()
    if row:
        return row[0]
    avatar = f"{name.lower()}.png"
    return upsert_player(conn, name, avatar_filename=avatar)


def upsert_week_data(
    conn: sqlite3.Connection,
    season_id: int,
    week: int,
    games: list[Game],
    player_results: list[PlayerResult],
) -> None:
    """Write all games, picks, and weekly results for one week.

    Deletes existing data for this season/week first (idempotent).
    """
    # Clear existing data for this week
    conn.execute(
        "DELETE FROM picks WHERE season_id = ? AND week = ?", (season_id, week)
    )
    conn.execute(
        "DELETE FROM weekly_results WHERE season_id = ? AND week = ?", (season_id, week)
    )
    conn.execute(
        "DELETE FROM games WHERE season_id = ? AND week = ?", (season_id, week)
    )

    # Insert games
    game_ids: dict[str, int] = {}
    for game in games:
        conn.execute(
            """INSERT INTO games (season_id, week, away_team, home_team, spread, tag, away_score, home_score)
               VALUES (?, ?, ?, ?, ?, ?, NULL, NULL)
               ON CONFLICT(season_id, week, away_team, home_team) DO NOTHING""",
            (season_id, week, game.away_team, game.home_team, game.spread, game.tag),
        )
        row = conn.execute(
            "SELECT id FROM games WHERE season_id = ? AND week = ? AND away_team = ? AND home_team = ?",
            (season_id, week, game.away_team, game.home_team),
        ).fetchone()
        game_ids[game.column_header] = row[0]

    # Insert player results and picks
    for pr in player_results:
        player_id = _get_or_create_player(conn, pr.name)

        # Weekly result
        conn.execute(
            """INSERT INTO weekly_results
               (season_id, week, player_id, correct, total, pushes, ats_bonus_team, ats_bonus_score)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                season_id, week, player_id,
                pr.correct, pr.total, pr.pushes,
                pr.ats_bonus_team, pr.ats_bonus_score,
            ),
        )

        # Individual picks
        for detail in pr.details:
            game_id = game_ids.get(detail.game.column_header)
            if game_id is None:
                continue

            # Update game scores from the detail (all details for the same game
            # have the same scores, so this is idempotent)
            conn.execute(
                "UPDATE games SET away_score = ?, home_score = ? WHERE id = ?",
                (detail.away_score, detail.home_score, game_id),
            )

            conn.execute(
                """INSERT INTO picks
                   (season_id, week, player_id, game_id, picked_team, picked_away, correct, push, ats_margin)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    season_id, week, player_id, game_id,
                    detail.picked, int(detail.picked_away),
                    int(detail.correct), int(detail.push), detail.ats_margin,
                ),
            )

    # Update weeks_available for this season
    rows = conn.execute(
        "SELECT DISTINCT week FROM weekly_results WHERE season_id = ? ORDER BY week",
        (season_id,),
    ).fetchall()
    weeks_json = json.dumps([r[0] for r in rows])
    conn.execute(
        "UPDATE seasons SET weeks_available = ? WHERE id = ?",
        (weeks_json, season_id),
    )

    conn.commit()


def recompute_season_standings(conn: sqlite3.Connection, season_id: int) -> None:
    """Rebuild the season_standings table from weekly_results for a season."""
    conn.execute(
        "DELETE FROM season_standings WHERE season_id = ?", (season_id,)
    )

    conn.execute(
        """INSERT INTO season_standings
           (season_id, player_id, weeks_played, total_correct, total_games, total_pushes,
            total_ats_bonus, win_pct, rank)
        SELECT
            season_id,
            player_id,
            COUNT(*) as weeks_played,
            SUM(correct) as total_correct,
            SUM(total) as total_games,
            SUM(pushes) as total_pushes,
            COALESCE(SUM(ats_bonus_score), 0.0) as total_ats_bonus,
            CASE WHEN SUM(total) - SUM(pushes) > 0
                 THEN CAST(SUM(correct) AS REAL) / (SUM(total) - SUM(pushes))
                 ELSE 0.0
            END as win_pct,
            NULL
        FROM weekly_results
        WHERE season_id = ?
        GROUP BY season_id, player_id""",
        (season_id,),
    )

    # Compute ranks (by total_correct desc, then total_ats_bonus desc)
    rows = conn.execute(
        """SELECT id, total_correct, total_ats_bonus
           FROM season_standings
           WHERE season_id = ?
           ORDER BY total_correct DESC, total_ats_bonus DESC""",
        (season_id,),
    ).fetchall()

    for rank, (row_id, _, _) in enumerate(rows, 1):
        conn.execute(
            "UPDATE season_standings SET rank = ? WHERE id = ?", (rank, row_id)
        )

    conn.commit()
