"use client";

import type { HeadToHeadData } from "@/lib/db";

interface Props {
  playerName: string;
  h2hData: HeadToHeadData[];
}

export default function HeadToHeadSection({ playerName, h2hData }: Props) {
  return (
    <div className="card">
      <h2 className="mb-3 text-lg font-bold">Head to Head</h2>
      <table className="data-table">
        <thead>
          <tr>
            <th>Opponent</th>
            <th>Weeks</th>
            <th>{playerName} Wins</th>
            <th>Opp Wins</th>
            <th>Ties</th>
          </tr>
        </thead>
        <tbody>
          {h2hData
            .filter((h) => h.weeksCompared > 0)
            .sort((a, b) => b.aWins - b.bWins - (a.aWins - a.bWins))
            .map((h) => (
              <tr key={h.playerB}>
                <td className="font-semibold">{h.playerB}</td>
                <td>{h.weeksCompared}</td>
                <td
                  className="font-bold"
                  style={{
                    color:
                      h.aWins > h.bWins
                        ? "var(--color-green)"
                        : h.aWins < h.bWins
                        ? "var(--color-red)"
                        : undefined,
                  }}
                >
                  {h.aWins}
                </td>
                <td className="font-bold">{h.bWins}</td>
                <td>{h.ties}</td>
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  );
}
