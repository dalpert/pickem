"use client";

import { useState } from "react";
import Link from "next/link";
import type { SeasonStanding, WeeklyRecord } from "@/lib/types";
import Avatar from "@/components/common/Avatar";
import { getPlayerColor } from "@/lib/colors";

type SortKey = "rank" | "wins" | "losses" | "pct";
type SortDir = "asc" | "desc";

interface Props {
  standings: SeasonStanding[];
  weeklyRecords: Record<number, WeeklyRecord[]>; // playerId -> records
  weeks: number[];
}

export default function StandingsTable({ standings, weeklyRecords, weeks }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>("rank");
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const sorted = [...standings].sort((a, b) => {
    let cmp = 0;
    switch (sortKey) {
      case "rank":
        cmp = a.rank - b.rank;
        break;
      case "wins":
        cmp = b.totalCorrect - a.totalCorrect;
        break;
      case "losses":
        cmp =
          b.totalGames - b.totalCorrect - b.totalPushes -
          (a.totalGames - a.totalCorrect - a.totalPushes);
        break;
      case "pct":
        cmp = b.winPct - a.winPct;
        break;
    }
    return sortDir === "desc" ? -cmp : cmp;
  });

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir(key === "rank" ? "asc" : "desc");
    }
  }

  const arrow = (key: SortKey) =>
    sortKey === key ? (sortDir === "asc" ? " ▲" : " ▼") : "";

  return (
    <table className="data-table">
      <thead>
        <tr>
          <th onClick={() => toggleSort("rank")}>#{ arrow("rank")}</th>
          <th>Player</th>
          <th onClick={() => toggleSort("wins")}>W{arrow("wins")}</th>
          <th onClick={() => toggleSort("losses")}>L{arrow("losses")}</th>
          <th>P</th>
          <th onClick={() => toggleSort("pct")}>Win %{arrow("pct")}</th>
        </tr>
      </thead>
      <tbody>
        {sorted.map((s, i) => {
          const losses = s.totalGames - s.totalCorrect - s.totalPushes;
          const expanded = expandedId === s.playerId;
          const records = weeklyRecords[s.playerId] ?? [];

          return (
            <>
              <tr
                key={s.playerId}
                className="expandable-row"
                onClick={() => setExpandedId(expanded ? null : s.playerId)}
              >
                <td className="font-bold text-[var(--color-text-muted)]">{s.rank}</td>
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
                <td className="font-bold">{s.totalCorrect}</td>
                <td>{losses}</td>
                <td>{s.totalPushes}</td>
                <td>{(s.winPct * 100).toFixed(1)}%</td>
              </tr>
              {expanded && (
                <tr key={`detail-${s.playerId}`} className="detail-row">
                  <td colSpan={6}>
                    <div className="wr-grid">
                      {records.map((r) => (
                        <span key={r.week} className="wr-badge">
                          W{r.week}: {r.wins}-{r.losses}
                          {r.pushes > 0 ? `-${r.pushes}` : ""}
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
