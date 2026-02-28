"use client";

import type { WeeklyResult, PickData, GameData } from "@/lib/types";

interface WeekData {
  week: number;
  results: WeeklyResult[];
  picks: Record<number, PickData[]>; // playerId -> picks
}

interface Props {
  weeksData: WeekData[];
}

export default function WeekResults({ weeksData }: Props) {
  return (
    <div className="space-y-2">
      {[...weeksData].reverse().map((wd) => {
        const winner = wd.results[0];
        const losses = winner ? winner.total - winner.correct - winner.pushes : 0;

        return (
          <details key={wd.week} className="week-card card !p-0">
            <summary>
              <span className="font-bold">Week {wd.week}</span>
              {winner && (
                <span className="text-sm text-[var(--color-text-muted)]">
                  — {winner.playerName} ({winner.correct}-{losses}
                  {winner.pushes > 0 ? `-${winner.pushes}` : ""})
                </span>
              )}
            </summary>
            <div className="week-content">
              <div className="pick-grid">
                {wd.results.map((r) => {
                  const playerPicks = wd.picks[r.playerId] ?? [];
                  const rLosses = r.total - r.correct - r.pushes;
                  return (
                    <div key={r.playerId} className="pick-card">
                      <div className="pick-card-header">
                        <span>{r.playerName}</span>
                        <span className="text-[var(--color-text-muted)] font-normal">
                          {r.correct}-{rLosses}
                          {r.pushes > 0 ? `-${r.pushes}` : ""}
                        </span>
                      </div>
                      {playerPicks.map((p) => {
                        const icon = p.push ? "⊘" : p.correct ? "✓" : "✗";
                        const cls = p.push
                          ? "pick-push"
                          : p.correct
                          ? "pick-correct"
                          : "pick-wrong";
                        const spreadStr =
                          p.game.spread >= 0
                            ? `+${p.game.spread}`
                            : String(p.game.spread);
                        return (
                          <div key={p.id} className={`pick-item ${cls}`}>
                            <span>{icon}</span>
                            <span>
                              {p.pickedTeam}
                              {p.game.tag ? ` [${p.game.tag}]` : ""}
                            </span>
                            <span className="text-[var(--color-text-muted)] text-xs ml-auto">
                              {p.push
                                ? "PUSH"
                                : `${p.atsMargin >= 0 ? "+" : ""}${p.atsMargin.toFixed(1)}`}
                            </span>
                          </div>
                        );
                      })}
                      {r.atsBonusTeam && (
                        <div className="mt-1 border-t border-[var(--color-border)] pt-1 text-xs text-[var(--color-text-muted)]">
                          ATS: {r.atsBonusTeam}
                          {r.atsBonusScore != null && (
                            <span
                              className="ml-1 font-semibold"
                              style={{
                                color:
                                  r.atsBonusScore >= 0
                                    ? "var(--color-green)"
                                    : "var(--color-red)",
                              }}
                            >
                              ({r.atsBonusScore >= 0 ? "+" : ""}
                              {r.atsBonusScore.toFixed(1)})
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </details>
        );
      })}
    </div>
  );
}
