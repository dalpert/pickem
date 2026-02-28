export interface Season {
  id: number;
  label: string;
  sheetId: string | null;
  weeksAvailable: number[];
}

export interface Player {
  id: number;
  name: string;
  email: string | null;
  avatarFilename: string | null;
}

export interface GameData {
  id: number;
  seasonId: number;
  week: number;
  awayTeam: string;
  homeTeam: string;
  spread: number;
  tag: string | null;
  awayScore: number | null;
  homeScore: number | null;
}

export interface PickData {
  id: number;
  gameId: number;
  pickedTeam: string;
  pickedAway: boolean;
  correct: boolean;
  push: boolean;
  atsMargin: number;
  game: GameData;
}

export interface WeeklyResult {
  seasonId: number;
  week: number;
  playerId: number;
  playerName: string;
  correct: number;
  total: number;
  pushes: number;
  atsBonusTeam: string | null;
  atsBonusScore: number | null;
  picks?: PickData[];
}

export interface SeasonStanding {
  seasonId: number;
  playerId: number;
  playerName: string;
  avatarFilename: string | null;
  weeksPlayed: number;
  totalCorrect: number;
  totalGames: number;
  totalPushes: number;
  totalAtsBonus: number;
  winPct: number;
  rank: number;
}

export interface WeeklyRecord {
  week: number;
  wins: number;
  losses: number;
  pushes: number;
}

export interface ChartPlayerData {
  name: string;
  color: string;
  values: number[];
  avatarUrl: string;
}

export interface PlayerCareerStats {
  player: Player;
  seasons: SeasonStanding[];
  totalCorrect: number;
  totalGames: number;
  totalPushes: number;
  totalAtsBonus: number;
  totalWeeksPlayed: number;
  careerWinPct: number;
}
