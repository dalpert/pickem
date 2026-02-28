import Database from "better-sqlite3";
import path from "path";
import type {
  Season,
  Player,
  SeasonStanding,
  WeeklyResult,
  WeeklyRecord,
  GameData,
  PickData,
  ChartPlayerData,
  PlayerCareerStats,
} from "./types";
import { getPlayerColor } from "./colors";

let _db: Database.Database | null = null;

function getDb(): Database.Database {
  if (!_db) {
    const dbPath = path.join(process.cwd(), "data", "pickem.db");
    _db = new Database(dbPath, { readonly: true });
    _db.pragma("journal_mode = WAL");
  }
  return _db;
}

// ─── Seasons ─────────────────────────────────────────────────────────

export function getSeasons(): Season[] {
  const db = getDb();
  const rows = db
    .prepare("SELECT id, label, sheet_id, weeks_available FROM seasons ORDER BY id DESC")
    .all() as { id: number; label: string; sheet_id: string | null; weeks_available: string }[];

  return rows.map((r) => ({
    id: r.id,
    label: r.label,
    sheetId: r.sheet_id,
    weeksAvailable: JSON.parse(r.weeks_available) as number[],
  }));
}

export function getSeason(seasonId: number): Season | null {
  const db = getDb();
  const row = db
    .prepare("SELECT id, label, sheet_id, weeks_available FROM seasons WHERE id = ?")
    .get(seasonId) as { id: number; label: string; sheet_id: string | null; weeks_available: string } | undefined;

  if (!row) return null;
  return {
    id: row.id,
    label: row.label,
    sheetId: row.sheet_id,
    weeksAvailable: JSON.parse(row.weeks_available) as number[],
  };
}

export function getLatestSeasonId(): number | null {
  const db = getDb();
  const row = db.prepare("SELECT MAX(id) as id FROM seasons").get() as { id: number | null };
  return row?.id ?? null;
}

// ─── Players ─────────────────────────────────────────────────────────

export function getPlayers(): Player[] {
  const db = getDb();
  return db.prepare("SELECT id, name, email, avatar_filename FROM players ORDER BY name").all() as Player[];
}

export function getPlayerByName(name: string): Player | null {
  const db = getDb();
  const row = db
    .prepare("SELECT id, name, email, avatar_filename FROM players WHERE LOWER(name) = LOWER(?)")
    .get(name) as { id: number; name: string; email: string | null; avatar_filename: string | null } | undefined;
  if (!row) return null;
  return { id: row.id, name: row.name, email: row.email, avatarFilename: row.avatar_filename };
}

// ─── Season Standings ────────────────────────────────────────────────

export function getSeasonStandings(seasonId: number): SeasonStanding[] {
  const db = getDb();
  const rows = db
    .prepare(
      `SELECT ss.season_id, ss.player_id, p.name, p.avatar_filename,
              ss.weeks_played, ss.total_correct, ss.total_games, ss.total_pushes,
              ss.total_ats_bonus, ss.win_pct, ss.rank
       FROM season_standings ss
       JOIN players p ON p.id = ss.player_id
       WHERE ss.season_id = ?
       ORDER BY ss.rank`
    )
    .all(seasonId) as {
    season_id: number;
    player_id: number;
    name: string;
    avatar_filename: string | null;
    weeks_played: number;
    total_correct: number;
    total_games: number;
    total_pushes: number;
    total_ats_bonus: number;
    win_pct: number;
    rank: number;
  }[];

  return rows.map((r) => ({
    seasonId: r.season_id,
    playerId: r.player_id,
    playerName: r.name,
    avatarFilename: r.avatar_filename,
    weeksPlayed: r.weeks_played,
    totalCorrect: r.total_correct,
    totalGames: r.total_games,
    totalPushes: r.total_pushes,
    totalAtsBonus: r.total_ats_bonus,
    winPct: r.win_pct,
    rank: r.rank,
  }));
}

// ─── Weekly Results ──────────────────────────────────────────────────

export function getWeeklyResults(seasonId: number, week: number): WeeklyResult[] {
  const db = getDb();
  const rows = db
    .prepare(
      `SELECT wr.season_id, wr.week, wr.player_id, p.name, wr.correct, wr.total,
              wr.pushes, wr.ats_bonus_team, wr.ats_bonus_score
       FROM weekly_results wr
       JOIN players p ON p.id = wr.player_id
       WHERE wr.season_id = ? AND wr.week = ?
       ORDER BY wr.correct DESC, wr.ats_bonus_score DESC`
    )
    .all(seasonId, week) as {
    season_id: number;
    week: number;
    player_id: number;
    name: string;
    correct: number;
    total: number;
    pushes: number;
    ats_bonus_team: string | null;
    ats_bonus_score: number | null;
  }[];

  return rows.map((r) => ({
    seasonId: r.season_id,
    week: r.week,
    playerId: r.player_id,
    playerName: r.name,
    correct: r.correct,
    total: r.total,
    pushes: r.pushes,
    atsBonusTeam: r.ats_bonus_team,
    atsBonusScore: r.ats_bonus_score,
  }));
}

export function getPlayerWeeklyRecords(
  seasonId: number,
  playerId: number
): WeeklyRecord[] {
  const db = getDb();
  const rows = db
    .prepare(
      `SELECT week, correct as wins,
              total - correct - pushes as losses, pushes
       FROM weekly_results
       WHERE season_id = ? AND player_id = ?
       ORDER BY week`
    )
    .all(seasonId, playerId) as {
    week: number;
    wins: number;
    losses: number;
    pushes: number;
  }[];

  return rows;
}

// ─── Games & Picks ───────────────────────────────────────────────────

export function getGamesForWeek(seasonId: number, week: number): GameData[] {
  const db = getDb();
  const rows = db
    .prepare(
      `SELECT id, season_id, week, away_team, home_team, spread, tag, away_score, home_score
       FROM games WHERE season_id = ? AND week = ?
       ORDER BY id`
    )
    .all(seasonId, week) as {
    id: number;
    season_id: number;
    week: number;
    away_team: string;
    home_team: string;
    spread: number;
    tag: string | null;
    away_score: number | null;
    home_score: number | null;
  }[];

  return rows.map((r) => ({
    id: r.id,
    seasonId: r.season_id,
    week: r.week,
    awayTeam: r.away_team,
    homeTeam: r.home_team,
    spread: r.spread,
    tag: r.tag,
    awayScore: r.away_score,
    homeScore: r.home_score,
  }));
}

export function getPlayerPicksForWeek(
  seasonId: number,
  week: number,
  playerId: number
): PickData[] {
  const db = getDb();
  const rows = db
    .prepare(
      `SELECT p.id, p.game_id, p.picked_team, p.picked_away, p.correct, p.push, p.ats_margin,
              g.season_id, g.week, g.away_team, g.home_team, g.spread, g.tag, g.away_score, g.home_score
       FROM picks p
       JOIN games g ON g.id = p.game_id
       WHERE p.season_id = ? AND p.week = ? AND p.player_id = ?
       ORDER BY g.id`
    )
    .all(seasonId, week, playerId) as {
    id: number;
    game_id: number;
    picked_team: string;
    picked_away: number;
    correct: number;
    push: number;
    ats_margin: number;
    season_id: number;
    week: number;
    away_team: string;
    home_team: string;
    spread: number;
    tag: string | null;
    away_score: number | null;
    home_score: number | null;
  }[];

  return rows.map((r) => ({
    id: r.id,
    gameId: r.game_id,
    pickedTeam: r.picked_team,
    pickedAway: !!r.picked_away,
    correct: !!r.correct,
    push: !!r.push,
    atsMargin: r.ats_margin,
    game: {
      id: r.game_id,
      seasonId: r.season_id,
      week: r.week,
      awayTeam: r.away_team,
      homeTeam: r.home_team,
      spread: r.spread,
      tag: r.tag,
      awayScore: r.away_score,
      homeScore: r.home_score,
    },
  }));
}

// ─── Chart Data ──────────────────────────────────────────────────────

export function getCumulativeWins(seasonId: number): ChartPlayerData[] {
  const db = getDb();
  const season = getSeason(seasonId);
  if (!season) return [];
  const weeks = season.weeksAvailable;

  const standings = getSeasonStandings(seasonId);

  return standings.map((s, idx) => {
    let cumulative = 0;
    const values = weeks.map((week) => {
      const row = db
        .prepare(
          "SELECT correct FROM weekly_results WHERE season_id = ? AND week = ? AND player_id = ?"
        )
        .get(seasonId, week, s.playerId) as { correct: number } | undefined;
      if (row) cumulative += row.correct;
      return cumulative;
    });

    return {
      name: s.playerName,
      color: getPlayerColor(idx),
      values,
      avatarUrl: s.avatarFilename ? `/avatars/${s.avatarFilename}` : "",
    };
  });
}

export function getCumulativeAts(seasonId: number): ChartPlayerData[] {
  const db = getDb();
  const season = getSeason(seasonId);
  if (!season) return [];
  const weeks = season.weeksAvailable;

  const standings = getSeasonStandings(seasonId);

  return standings.map((s, idx) => {
    let cumulative = 0;
    const values = weeks.map((week) => {
      const row = db
        .prepare(
          "SELECT ats_bonus_score FROM weekly_results WHERE season_id = ? AND week = ? AND player_id = ?"
        )
        .get(seasonId, week, s.playerId) as { ats_bonus_score: number | null } | undefined;
      if (row?.ats_bonus_score != null) cumulative += row.ats_bonus_score;
      return cumulative;
    });

    return {
      name: s.playerName,
      color: getPlayerColor(idx),
      values,
      avatarUrl: s.avatarFilename ? `/avatars/${s.avatarFilename}` : "",
    };
  });
}

// ─── Player Career Stats ─────────────────────────────────────────────

export function getPlayerCareerStats(playerId: number): PlayerCareerStats | null {
  const db = getDb();
  const player = db
    .prepare("SELECT id, name, email, avatar_filename FROM players WHERE id = ?")
    .get(playerId) as { id: number; name: string; email: string | null; avatar_filename: string | null } | undefined;

  if (!player) return null;

  const seasons = db
    .prepare(
      `SELECT ss.season_id, ss.player_id, p.name, p.avatar_filename,
              ss.weeks_played, ss.total_correct, ss.total_games, ss.total_pushes,
              ss.total_ats_bonus, ss.win_pct, ss.rank
       FROM season_standings ss
       JOIN players p ON p.id = ss.player_id
       WHERE ss.player_id = ?
       ORDER BY ss.season_id DESC`
    )
    .all(playerId) as {
    season_id: number;
    player_id: number;
    name: string;
    avatar_filename: string | null;
    weeks_played: number;
    total_correct: number;
    total_games: number;
    total_pushes: number;
    total_ats_bonus: number;
    win_pct: number;
    rank: number;
  }[];

  const seasonStandings: SeasonStanding[] = seasons.map((r) => ({
    seasonId: r.season_id,
    playerId: r.player_id,
    playerName: r.name,
    avatarFilename: r.avatar_filename,
    weeksPlayed: r.weeks_played,
    totalCorrect: r.total_correct,
    totalGames: r.total_games,
    totalPushes: r.total_pushes,
    totalAtsBonus: r.total_ats_bonus,
    winPct: r.win_pct,
    rank: r.rank,
  }));

  const totalCorrect = seasonStandings.reduce((s, r) => s + r.totalCorrect, 0);
  const totalGames = seasonStandings.reduce((s, r) => s + r.totalGames, 0);
  const totalPushes = seasonStandings.reduce((s, r) => s + r.totalPushes, 0);
  const totalAtsBonus = seasonStandings.reduce((s, r) => s + r.totalAtsBonus, 0);
  const totalWeeksPlayed = seasonStandings.reduce((s, r) => s + r.weeksPlayed, 0);
  const decided = totalGames - totalPushes;

  return {
    player: {
      id: player.id,
      name: player.name,
      email: player.email,
      avatarFilename: player.avatar_filename,
    },
    seasons: seasonStandings,
    totalCorrect,
    totalGames,
    totalPushes,
    totalAtsBonus,
    totalWeeksPlayed,
    careerWinPct: decided > 0 ? totalCorrect / decided : 0,
  };
}

export function getAllPlayerCareerStats(): PlayerCareerStats[] {
  const players = getPlayers();
  return players
    .map((p) => getPlayerCareerStats(p.id))
    .filter((s): s is PlayerCareerStats => s !== null && s.seasons.length > 0);
}

// ─── Head to Head ────────────────────────────────────────────────────

export interface HeadToHeadData {
  playerA: string;
  playerB: string;
  weeksCompared: number;
  aWins: number;
  bWins: number;
  ties: number;
}

export function getHeadToHead(playerAId: number, playerBId: number): HeadToHeadData {
  const db = getDb();

  const playerA = db.prepare("SELECT name FROM players WHERE id = ?").get(playerAId) as { name: string };
  const playerB = db.prepare("SELECT name FROM players WHERE id = ?").get(playerBId) as { name: string };

  const rows = db
    .prepare(
      `SELECT a.season_id, a.week, a.correct as a_correct, b.correct as b_correct
       FROM weekly_results a
       JOIN weekly_results b ON a.season_id = b.season_id AND a.week = b.week
       WHERE a.player_id = ? AND b.player_id = ?
       ORDER BY a.season_id, a.week`
    )
    .all(playerAId, playerBId) as {
    season_id: number;
    week: number;
    a_correct: number;
    b_correct: number;
  }[];

  let aWins = 0;
  let bWins = 0;
  let ties = 0;
  for (const r of rows) {
    if (r.a_correct > r.b_correct) aWins++;
    else if (r.b_correct > r.a_correct) bWins++;
    else ties++;
  }

  return {
    playerA: playerA.name,
    playerB: playerB.name,
    weeksCompared: rows.length,
    aWins,
    bWins,
    ties,
  };
}
