export const PLAYER_COLORS = [
  "#4a7c96",
  "#c0504d",
  "#3d8b5e",
  "#7b6b9e",
  "#c98442",
  "#5a9e9e",
  "#8b7d42",
  "#96506e",
];

export function getPlayerColor(index: number): string {
  return PLAYER_COLORS[index % PLAYER_COLORS.length];
}
