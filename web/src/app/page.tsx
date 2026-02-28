import Link from "next/link";
import { getSeasons, getSeasonStandings, getAllPlayerCareerStats } from "@/lib/db";
import Avatar from "@/components/common/Avatar";
import { getPlayerColor } from "@/lib/colors";

export default function HomePage() {
  const seasons = getSeasons();
  const latestSeason = seasons[0];
  const standings = latestSeason ? getSeasonStandings(latestSeason.id) : [];
  const careerStats = getAllPlayerCareerStats();

  return (
    <div className="space-y-8">
      {/* Hero */}
      <header className="text-center">
        <h1 className="text-3xl font-extrabold tracking-tight">Pick&apos;em Results</h1>
        <p className="mt-1 text-[var(--color-text-muted)]">
          NFL pick&apos;em pool &middot; {seasons.length} season{seasons.length !== 1 ? "s" : ""} of data
        </p>
      </header>

      {/* Current Season */}
      {latestSeason && (
        <section className="card">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-bold">
              {latestSeason.label} Season
            </h2>
            <Link
              href={`/seasons/${latestSeason.id}`}
              className="text-sm font-semibold text-[var(--color-accent)] no-underline hover:underline"
            >
              Full Season →
            </Link>
          </div>

          <table className="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Player</th>
                <th>W</th>
                <th>L</th>
                <th>Win %</th>
                <th>ATS</th>
              </tr>
            </thead>
            <tbody>
              {standings.map((s, i) => (
                <tr key={s.playerId}>
                  <td className="font-bold text-[var(--color-text-muted)]">{s.rank}</td>
                  <td>
                    <Link
                      href={`/players/${s.playerName.toLowerCase()}`}
                      className="flex items-center gap-2 no-underline text-[var(--color-text)]"
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
                  <td>{s.totalGames - s.totalCorrect - s.totalPushes}</td>
                  <td>{(s.winPct * 100).toFixed(1)}%</td>
                  <td
                    className="font-semibold"
                    style={{
                      color: s.totalAtsBonus >= 0 ? "var(--color-green)" : "var(--color-red)",
                    }}
                  >
                    {s.totalAtsBonus >= 0 ? "+" : ""}
                    {s.totalAtsBonus.toFixed(1)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {/* Season Links */}
      <section className="card">
        <h2 className="mb-4 text-lg font-bold">All Seasons</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
          {seasons.map((s) => {
            const seasonStandings = getSeasonStandings(s.id);
            const winner = seasonStandings[0];
            return (
              <Link
                key={s.id}
                href={`/seasons/${s.id}`}
                className="flex flex-col items-center gap-2 rounded-lg border border-[var(--color-border)] p-4 no-underline transition hover:border-[var(--color-accent)] hover:shadow-md"
              >
                <span className="text-lg font-bold text-[var(--color-text)]">{s.label}</span>
                {winner && (
                  <span className="text-xs text-[var(--color-text-muted)]">
                    Won by {winner.playerName}
                  </span>
                )}
                <span className="text-xs text-[var(--color-text-muted)]">
                  {s.weeksAvailable.length} weeks
                </span>
              </Link>
            );
          })}
        </div>
      </section>

      {/* Player Quick Links */}
      <section className="card">
        <h2 className="mb-4 text-lg font-bold">Players</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
          {careerStats.map((cs, i) => (
            <Link
              key={cs.player.id}
              href={`/players/${cs.player.name.toLowerCase()}`}
              className="flex items-center gap-3 rounded-lg border border-[var(--color-border)] p-3 no-underline transition hover:border-[var(--color-accent)] hover:shadow-md"
            >
              <Avatar
                name={cs.player.name}
                avatarFilename={cs.player.avatarFilename}
                color={getPlayerColor(i)}
              />
              <div>
                <div className="font-semibold text-[var(--color-text)]">{cs.player.name}</div>
                <div className="text-xs text-[var(--color-text-muted)]">
                  {cs.totalCorrect}-{cs.totalGames - cs.totalCorrect - cs.totalPushes}
                  {" · "}
                  {(cs.careerWinPct * 100).toFixed(1)}%
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
