"use client";

import { useState } from "react";
import Link from "next/link";
import type { SeasonStanding } from "@/lib/types";
import Avatar from "@/components/common/Avatar";
import { getPlayerColor } from "@/lib/colors";

interface AtsWeekDetail {
  week: number;
  team: string | null;
  score: number | null;
}

interface Props {
  standings: SeasonStanding[];
  atsDetails: Record<number, AtsWeekDetail[]>; // playerId -> weekly ATS details
}

export default function AtsLeaderboard({ standings, atsDetails }: Props) {
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const sorted = [...standings].sort(
    (a, b) => b.totalAtsBonus - a.totalAtsBonus
  );

  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>#</th>
          <th>Player</th>
          <th>ATS Total</th>
        </tr>
      </thead>
      <tbody>
        {sorted.map((s, i) => {
          const expanded = expandedId === s.playerId;
          const details = atsDetails[s.playerId] ?? [];

          return (
            <>
              <tr
                key={s.playerId}
                className="expandable-row"
                onClick={() => setExpandedId(expanded ? null : s.playerId)}
              >
                <td className="font-bold text-[var(--color-text-muted)]">{i + 1}</td>
                <td>
                  <Link
                    href={`/players/${s.playerName.toLowerCase()}`}
                    className="flex items-center gap-2 no-underline text-[var(--color-text)]"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <Avatar
                      name={s.playerName}
                      avatarFilename={s.avatarFilename}
                      color={getPlayerColor(i)}
                      size="sm"
                    />
                    <span className="font-semibold">{s.playerName}</span>
                  </Link>
                </td>
                <td
                  className="font-bold"
                  style={{
                    color:
                      s.totalAtsBonus >= 0
                        ? "var(--color-green)"
                        : "var(--color-red)",
                  }}
                >
                  {s.totalAtsBonus >= 0 ? "+" : ""}
                  {s.totalAtsBonus.toFixed(1)}
                </td>
              </tr>
              {expanded && (
                <tr key={`ats-detail-${s.playerId}`} className="detail-row">
                  <td colSpan={3}>
                    <div className="wr-grid">
                      {details.map((d) => (
                        <span
                          key={d.week}
                          className="wr-badge"
                          style={{
                            color:
                              d.score != null && d.score >= 0
                                ? "var(--color-green)"
                                : d.score != null
                                ? "var(--color-red)"
                                : undefined,
                          }}
                        >
                          W{d.week}: {d.team ?? "—"}{" "}
                          {d.score != null
                            ? `(${d.score >= 0 ? "+" : ""}${d.score.toFixed(1)})`
                            : ""}
                        </span>
                      ))}
                    </div>
                  </td>
                </tr>
              )}
            </>
          );
        })}
      </tbody>
    </table>
  );
}
