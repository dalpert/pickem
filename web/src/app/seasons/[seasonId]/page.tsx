import { notFound } from "next/navigation";
import {
  getSeasons,
  getSeason,
  getSeasonStandings,
  getPlayerWeeklyRecords,
  getCumulativeWins,
  getCumulativeAts,
  getWeeklyResults,
  getPlayerPicksForWeek,
} from "@/lib/db";
import type { WeeklyRecord, WeeklyResult, PickData } from "@/lib/types";
import StandingsTable from "@/components/tables/StandingsTable";
import AtsLeaderboard from "@/components/tables/AtsLeaderboard";
import BarChartRace from "@/components/charts/BarChartRace";
import AtsChartRace from "@/components/charts/AtsChartRace";
import WeekResults from "@/components/tables/WeekResults";

export function generateStaticParams() {
  return getSeasons().map((s) => ({ seasonId: String(s.id) }));
}

export function generateMetadata({ params }: { params: Promise<{ seasonId: string }> }) {
  return params.then((p) => {
    const season = getSeason(Number(p.seasonId));
    return { title: season ? `${season.label} — Pick'em` : "Season — Pick'em" };
  });
}

export default async function SeasonPage({
  params,
}: {
  params: Promise<{ seasonId: string }>;
}) {
  const { seasonId: seasonIdStr } = await params;
  const seasonId = Number(seasonIdStr);
  const season = getSeason(seasonId);
  if (!season) notFound();

  const standings = getSeasonStandings(seasonId);
  const weeks = season.weeksAvailable;

  // Weekly records for standings expandable rows
  const weeklyRecords: Record<number, WeeklyRecord[]> = {};
  standings.forEach((s) => {
    weeklyRecords[s.playerId] = getPlayerWeeklyRecords(seasonId, s.playerId);
  });

  // Chart data
  const winsData = getCumulativeWins(seasonId);
  const atsData = getCumulativeAts(seasonId);

  // ATS details for leaderboard expandable rows
  const atsDetails: Record<number, { week: number; team: string | null; score: number | null }[]> = {};
  standings.forEach((s) => {
    atsDetails[s.playerId] = weeks.map((week) => {
      const results = getWeeklyResults(seasonId, week);
      const r = results.find((wr) => wr.playerId === s.playerId);
      return {
        week,
        team: r?.atsBonusTeam ?? null,
        score: r?.atsBonusScore ?? null,
      };
    });
  });

  // Week-by-week detailed data
  const weeksData = weeks.map((week) => {
    const results = getWeeklyResults(seasonId, week);
    const picks: Record<number, PickData[]> = {};
    results.forEach((r) => {
      picks[r.playerId] = getPlayerPicksForWeek(seasonId, week, r.playerId);
    });
    return { week, results, picks };
  });

  return (
    <div className="space-y-8">
      <header className="text-center">
        <h1 className="text-2xl font-extrabold">{season.label} NFL Season</h1>
        <p className="text-[var(--color-text-muted)]">
          Weeks {weeks[0]}-{weeks[weeks.length - 1]}
        </p>
      </header>

      <BarChartRace
        data={winsData}
        weeks={weeks}
        title="Most Wins"
        idPrefix="wins"
      />

      <section className="card">
        <h2 className="mb-3 text-lg font-bold">Season Standings</h2>
        <StandingsTable
          standings={standings}
          weeklyRecords={weeklyRecords}
          weeks={weeks}
        />
      </section>

      <AtsChartRace data={atsData} weeks={weeks} />

      <section className="card">
        <h2 className="mb-3 text-lg font-bold">ATS Bonus Leaderboard</h2>
        <AtsLeaderboard standings={standings} atsDetails={atsDetails} />
      </section>

      <section>
        <h2 className="mb-3 text-lg font-bold">Week-by-Week Results</h2>
        <WeekResults weeksData={weeksData} />
      </section>
    </div>
  );
}
