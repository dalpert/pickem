import { notFound } from "next/navigation";
import Link from "next/link";
import {
  getPlayers,
  getPlayerByName,
  getPlayerCareerStats,
  getSeasons,
  getPlayerWeeklyRecords,
  getHeadToHead,
} from "@/lib/db";
import Avatar from "@/components/common/Avatar";
import { getPlayerColor } from "@/lib/colors";
import HeadToHeadSection from "@/components/player/HeadToHeadSection";

export function generateStaticParams() {
  return getPlayers().map((p) => ({ playerName: p.name.toLowerCase() }));
}

export function generateMetadata({ params }: { params: Promise<{ playerName: string }> }) {
  return params.then((p) => {
    const player = getPlayerByName(p.playerName);
    return { title: player ? `${player.name} — Pick'em` : "Player — Pick'em" };
  });
}

export default async function PlayerPage({
  params,
}: {
  params: Promise<{ playerName: string }>;
}) {
  const { playerName } = await params;
  const player = getPlayerByName(playerName);
  if (!player) notFound();

  const career = getPlayerCareerStats(player.id);
  if (!career) notFound();

  const seasons = getSeasons();
  const allPlayers = getPlayers();
  const otherPlayers = allPlayers.filter((p) => p.id !== player.id);

  // Head-to-head data for all opponents
  const h2hData = otherPlayers.map((op) => getHeadToHead(player.id, op.id));

  // Season-by-season weekly records
  const seasonRecords: Record<number, { week: number; wins: number; losses: number; pushes: number }[]> = {};
  career.seasons.forEach((s) => {
    seasonRecords[s.seasonId] = getPlayerWeeklyRecords(s.seasonId, player.id);
  });

  const totalLosses = career.totalGames - career.totalCorrect - career.totalPushes;

  return (
    <div className="space-y-6">
      {/* Profile header */}
      <div className="card flex items-center gap-5">
        <Avatar
          name={player.name}
          avatarFilename={player.avatarFilename}
          color={getPlayerColor(0)}
          size="lg"
        />
        <div>
          <h1 className="text-2xl font-extrabold">{player.name}</h1>
          <p className="text-[var(--color-text-muted)]">
            {career.seasons.length} season{career.seasons.length !== 1 ? "s" : ""}
            {" · "}
            {career.totalWeeksPlayed} weeks played
          </p>
        </div>
      </div>

      {/* Career stats */}
      <div className="card">
        <h2 className="mb-3 text-lg font-bold">Career Stats</h2>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div>
            <div className="text-2xl font-extrabold">{career.totalCorrect}-{totalLosses}</div>
            <div className="text-xs text-[var(--color-text-muted)]">Record</div>
          </div>
          <div>
            <div className="text-2xl font-extrabold">{(career.careerWinPct * 100).toFixed(1)}%</div>
            <div className="text-xs text-[var(--color-text-muted)]">Win %</div>
          </div>
          <div>
            <div
              className="text-2xl font-extrabold"
              style={{
                color: career.totalAtsBonus >= 0 ? "var(--color-green)" : "var(--color-red)",
              }}
            >
              {career.totalAtsBonus >= 0 ? "+" : ""}{career.totalAtsBonus.toFixed(1)}
            </div>
            <div className="text-xs text-[var(--color-text-muted)]">Career ATS</div>
          </div>
          <div>
            <div className="text-2xl font-extrabold">{career.totalWeeksPlayed}</div>
            <div className="text-xs text-[var(--color-text-muted)]">Weeks Played</div>
          </div>
        </div>
      </div>

      {/* Season-by-season */}
      <div className="card">
        <h2 className="mb-3 text-lg font-bold">Season Breakdown</h2>
        <table className="data-table">
          <thead>
            <tr>
              <th>Season</th>
              <th>W</th>
              <th>L</th>
              <th>Win %</th>
              <th>ATS</th>
              <th>Rank</th>
            </tr>
          </thead>
          <tbody>
            {career.seasons.map((s) => {
              const sLosses = s.totalGames - s.totalCorrect - s.totalPushes;
              const seasonLabel = seasons.find((se) => se.id === s.seasonId)?.label ?? String(s.seasonId);
              return (
                <tr key={s.seasonId}>
                  <td>
                    <Link
                      href={`/seasons/${s.seasonId}`}
                      className="font-semibold text-[var(--color-accent)] no-underline hover:underline"
                    >
                      {seasonLabel}
                    </Link>
                  </td>
                  <td className="font-bold">{s.totalCorrect}</td>
                  <td>{sLosses}</td>
                  <td>{(s.winPct * 100).toFixed(1)}%</td>
                  <td
                    className="font-semibold"
                    style={{
                      color: s.totalAtsBonus >= 0 ? "var(--color-green)" : "var(--color-red)",
                    }}
                  >
                    {s.totalAtsBonus >= 0 ? "+" : ""}{s.totalAtsBonus.toFixed(1)}
                  </td>
                  <td>
                    <span className="rounded-full bg-[var(--color-surface2)] px-2 py-0.5 text-xs font-bold">
                      #{s.rank}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Head to Head */}
      <HeadToHeadSection playerName={player.name} h2hData={h2hData} />
    </div>
  );
}
