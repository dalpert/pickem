import Link from "next/link";
import { getAllPlayerCareerStats, getSeasons } from "@/lib/db";
import Avatar from "@/components/common/Avatar";
import { getPlayerColor } from "@/lib/colors";

export const metadata = { title: "Players — Pick'em" };

export default function PlayersPage() {
  const stats = getAllPlayerCareerStats();
  const seasons = getSeasons();

  return (
    <div className="space-y-6">
      <header className="text-center">
        <h1 className="text-2xl font-extrabold">Players</h1>
        <p className="text-[var(--color-text-muted)]">
          Career stats across {seasons.length} season{seasons.length !== 1 ? "s" : ""}
        </p>
      </header>

      <div className="grid gap-4 sm:grid-cols-2">
        {stats
          .sort((a, b) => b.careerWinPct - a.careerWinPct)
          .map((cs, i) => {
            const losses = cs.totalGames - cs.totalCorrect - cs.totalPushes;
            return (
              <Link
                key={cs.player.id}
                href={`/players/${cs.player.name.toLowerCase()}`}
                className="card flex items-center gap-4 no-underline transition hover:shadow-md hover:border-[var(--color-accent)]"
              >
                <Avatar
                  name={cs.player.name}
                  avatarFilename={cs.player.avatarFilename}
                  color={getPlayerColor(i)}
                  size="lg"
                />
                <div className="flex-1">
                  <div className="text-lg font-bold text-[var(--color-text)]">
                    {cs.player.name}
                  </div>
                  <div className="text-sm text-[var(--color-text-muted)]">
                    {cs.seasons.length} season{cs.seasons.length !== 1 ? "s" : ""}
                    {" · "}
                    {cs.totalWeeksPlayed} weeks
                  </div>
                  <div className="mt-1 flex gap-4 text-sm">
                    <span>
                      <span className="font-bold">{cs.totalCorrect}</span>-
                      <span>{losses}</span>
                      {cs.totalPushes > 0 && (
                        <span>-{cs.totalPushes}</span>
                      )}
                    </span>
                    <span className="font-semibold">
                      {(cs.careerWinPct * 100).toFixed(1)}%
                    </span>
                    <span
                      className="font-semibold"
                      style={{
                        color:
                          cs.totalAtsBonus >= 0
                            ? "var(--color-green)"
                            : "var(--color-red)",
                      }}
                    >
                      {cs.totalAtsBonus >= 0 ? "+" : ""}
                      {cs.totalAtsBonus.toFixed(1)} ATS
                    </span>
                  </div>
                </div>
              </Link>
            );
          })}
      </div>
    </div>
  );
}
