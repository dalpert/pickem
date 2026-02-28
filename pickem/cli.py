from __future__ import annotations

import click
from tabulate import tabulate

from pickem.grader import grade_picks
from pickem.names import canonical_name
from pickem.parser import parse_responses
from pickem.scores import current_nfl_season, fetch_scores
from pickem.sheets import extract_sheet_id, fetch_responses, list_tabs, write_to_tab

DEFAULT_SHEET_ID = "1XLl5hB6t146fBuzUpl2SnywDyo9ddRrSwUUXnMzDmfE"


def _resolve_sheet(sheet_url: str | None, sheet_id: str | None) -> str:
    raw = sheet_url or sheet_id or DEFAULT_SHEET_ID
    return extract_sheet_id(raw)


@click.group()
def cli() -> None:
    """NFL Pick'em grader — grade your weekly picks against actual scores."""


@cli.command()
@click.option("--sheet-id", default=None, help="Google Spreadsheet ID (or full URL).")
@click.option("--sheet-url", default=None, help="Google Spreadsheet URL.")
@click.option("--tab", required=True, help="Tab/worksheet name for the week to grade.")
@click.option("--week", required=True, type=int, help="NFL week number (1-18).")
@click.option("--season", default=None, type=int, help="NFL season year. Defaults to current.")
@click.option("--leaderboard-only", is_flag=True, default=False)
@click.option("--no-cache", is_flag=True, default=False)
def grade(
    sheet_id: str | None,
    sheet_url: str | None,
    tab: str,
    week: int,
    season: int | None,
    leaderboard_only: bool,
    no_cache: bool,
) -> None:
    """Grade picks for a specific week."""
    sid = _resolve_sheet(sheet_url, sheet_id)
    if season is None:
        season = current_nfl_season()

    click.echo(f"Grading Week {week} ({season} season)...")
    click.echo()

    headers, rows = fetch_responses(sid, tab)
    games, players = parse_responses(headers, rows)
    click.echo(f"  Found {len(games)} games, {len(players)} players")

    results = fetch_scores(season, week, use_cache=not no_cache)
    click.echo(f"  {len(results)} completed games")
    click.echo()

    player_results = grade_picks(games, players, results)
    _print_leaderboard(week, player_results, leaderboard_only)


@cli.command()
@click.option("--sheet-id", default=None)
@click.option("--sheet-url", default=None)
def tabs(sheet_id: str | None, sheet_url: str | None) -> None:
    """List all tabs in the spreadsheet."""
    sid = _resolve_sheet(sheet_url, sheet_id)
    tab_names = list_tabs(sid)
    click.echo("Tabs in spreadsheet:")
    for name in tab_names:
        click.echo(f"  - {name}")


@cli.command()
@click.option("--week", required=True, type=int, help="NFL week number to export.")
@click.option("--form-url", default=None, help="Google Form URL.")
@click.option("--sheet-id", default=None)
@click.option("--sheet-url", default=None)
def export(
    week: int, form_url: str | None, sheet_id: str | None, sheet_url: str | None
) -> None:
    """Export one week's form responses to the spreadsheet."""
    from pickem.forms import export_form_to_rows, extract_form_id, find_pickem_form

    if form_url:
        form_id = extract_form_id(form_url)
    else:
        click.echo(f"Searching for Week {week} form...")
        form_info = find_pickem_form(week)
        if not form_info:
            raise click.ClickException(f"Could not find Week {week} form.")
        form_id = form_info["id"]
        click.echo(f"  Found: {form_info['name']}")

    click.echo("Reading form responses...")
    headers, rows = export_form_to_rows(form_id)
    click.echo(f"  {len(rows)} responses")

    sid = _resolve_sheet(sheet_url, sheet_id)
    tab_name = f"week{week}"
    click.echo(f"Writing to tab '{tab_name}'...")
    write_to_tab(sid, tab_name, headers, rows)
    click.echo(f"  Done! {len(rows)} rows written.")


@cli.command(name="export-all")
@click.option("--sheet-id", default=None)
@click.option("--sheet-url", default=None)
@click.option("--force", is_flag=True, default=False, help="Re-export even if tab exists.")
@click.option("--weeks", default="1-18", help="Week range, e.g. '1-18' or '11-14'.")
def export_all(
    sheet_id: str | None, sheet_url: str | None, force: bool, weeks: str
) -> None:
    """Export all weeks' form responses to the spreadsheet."""
    from pickem.forms import export_form_to_rows, find_pickem_form

    sid = _resolve_sheet(sheet_url, sheet_id)
    start, end = [int(x) for x in weeks.split("-")]

    existing_tabs = set(list_tabs(sid)) if not force else set()

    for week in range(start, end + 1):
        tab_name = f"week{week}"
        if tab_name in existing_tabs and not force:
            click.echo(f"Week {week}: tab '{tab_name}' exists, skipping (use --force)")
            continue

        form_info = find_pickem_form(week)
        if not form_info:
            click.echo(f"Week {week}: form not found, skipping")
            continue

        headers, rows = export_form_to_rows(form_info["id"])
        write_to_tab(sid, tab_name, headers, rows)
        click.echo(f"Week {week}: {len(rows)} responses → '{tab_name}'")


@cli.command()
@click.option("--sheet-id", default=None)
@click.option("--sheet-url", default=None)
@click.option("--season", default=None, type=int)
@click.option("--weeks", default="1-18", help="Week range, e.g. '1-18' or '11-14'.")
@click.option("--no-cache", is_flag=True, default=False)
@click.option("--output", default=None, type=click.Path(), help="HTML report output path.")
def report(
    sheet_id: str | None,
    sheet_url: str | None,
    season: int | None,
    weeks: str,
    no_cache: bool,
    output: str | None,
) -> None:
    """Grade all weeks and generate a season report.

    Reads from the spreadsheet, grades each week, and produces a leaderboard
    plus an optional HTML report.
    """
    from pickem.season import aggregate_season, print_season_summary
    from pickem.report import generate_report

    sid = _resolve_sheet(sheet_url, sheet_id)
    if season is None:
        season = current_nfl_season()

    start, end = [int(x) for x in weeks.split("-")]
    existing = set(list_tabs(sid))

    all_week_results = {}

    import time

    for week in range(start, end + 1):
        tab_name = f"week{week}"
        if tab_name not in existing:
            continue

        for attempt in range(3):
            try:
                headers, rows = fetch_responses(sid, tab_name)
                games, players = parse_responses(headers, rows)
                results = fetch_scores(season, week, use_cache=not no_cache)
                player_results = grade_picks(games, players, results)
                all_week_results[week] = (games, player_results)
                click.echo(f"Week {week}: graded {len(player_results)} players")
                break
            except Exception as e:
                if "429" in str(e) and attempt < 2:
                    click.echo(f"Week {week}: rate limited, retrying in {10 * (attempt + 1)}s...")
                    time.sleep(10 * (attempt + 1))
                else:
                    click.echo(f"Week {week}: ERROR - {e}")
                    break

    if not all_week_results:
        raise click.ClickException("No weeks could be graded.")

    season_data = aggregate_season(all_week_results)
    print_season_summary(season_data)

    if output:
        html = generate_report(season_data, all_week_results, season)
        with open(output, "w") as f:
            f.write(html)
        click.echo(f"\nHTML report written to {output}")


@cli.command()
@click.option("--sheet-id", default=None)
@click.option("--sheet-url", default=None)
@click.option("--season", required=True, type=int, help="NFL season year (e.g. 2024).")
@click.option("--weeks", default="1-18", help="Week range, e.g. '1-18' or '11-14'.")
@click.option("--no-cache", is_flag=True, default=False)
@click.option(
    "--db",
    default="pickem.db",
    type=click.Path(),
    help="Path to SQLite database file.",
)
@click.option("--label", default=None, help="Season label, e.g. '2024-25'. Auto-generated if omitted.")
def ingest(
    sheet_id: str | None,
    sheet_url: str | None,
    season: int,
    weeks: str,
    no_cache: bool,
    db: str,
    label: str | None,
) -> None:
    """Grade all weeks for a season and write results to SQLite."""
    from pickem.db import init_db, upsert_season, recompute_season_standings, upsert_week_data

    sid = _resolve_sheet(sheet_url, sheet_id)
    if label is None:
        label = f"{season}-{str(season + 1)[-2:]}"

    conn = init_db(db)
    upsert_season(conn, season, label, sid)

    start, end = [int(x) for x in weeks.split("-")]
    existing = set(list_tabs(sid))

    import time

    graded_weeks = 0
    for week in range(start, end + 1):
        tab_name = f"week{week}"
        if tab_name not in existing:
            continue

        for attempt in range(3):
            try:
                headers, rows = fetch_responses(sid, tab_name)
                games, players = parse_responses(headers, rows)
                results = fetch_scores(season, week, use_cache=not no_cache)
                player_results = grade_picks(games, players, results)
                upsert_week_data(conn, season, week, games, player_results)
                click.echo(f"Week {week}: ingested {len(player_results)} players, {len(games)} games")
                graded_weeks += 1
                break
            except Exception as e:
                if "429" in str(e) and attempt < 2:
                    click.echo(f"Week {week}: rate limited, retrying in {10 * (attempt + 1)}s...")
                    time.sleep(10 * (attempt + 1))
                else:
                    click.echo(f"Week {week}: ERROR - {e}")
                    break

    if graded_weeks == 0:
        conn.close()
        raise click.ClickException("No weeks could be graded.")

    recompute_season_standings(conn, season)
    conn.close()
    click.echo(f"\nDone! {graded_weeks} weeks ingested into {db}")


def _print_leaderboard(week: int, player_results, leaderboard_only: bool) -> None:
    click.echo("=" * 60)
    click.echo(f"  WEEK {week} LEADERBOARD")
    click.echo("=" * 60)

    table_data = []
    for i, pr in enumerate(player_results, 1):
        ats_str = f"{pr.ats_bonus_score:+.1f}" if pr.ats_bonus_score is not None else "N/A"
        ats_team_str = pr.ats_bonus_team or "N/A"
        record = f"{pr.correct}-{pr.losses}"
        if pr.pushes > 0:
            record += f"-{pr.pushes}P"
        table_data.append([
            i, pr.name, record, f"{pr.pct:.0%}",
            ats_team_str, ats_str,
        ])

    click.echo(tabulate(
        table_data,
        headers=["Rank", "Name", "Record", "Pct", "ATS Pick", "ATS Bonus"],
        tablefmt="simple",
    ))

    if leaderboard_only:
        return

    click.echo()
    for pr in player_results:
        click.echo("-" * 60)
        record = f"{pr.correct}-{pr.losses}"
        if pr.pushes > 0:
            record += f"-{pr.pushes}P"
        click.echo(f"  {pr.name}: {record}")
        click.echo("-" * 60)
        for detail in pr.details:
            if detail.push:
                check = "~"
            elif detail.correct:
                check = "+"
            else:
                check = "X"
            score_str = f"{detail.game.away_team} {detail.away_score}, {detail.game.home_team} {detail.home_score}"
            margin_str = f"(PUSH)" if detail.push else f"({detail.ats_margin:+.1f})"
            click.echo(f"  [{check}] Picked {detail.picked:<20s} {margin_str:>8s} | {score_str}")
        if pr.ats_bonus_team:
            ats_str = f"{pr.ats_bonus_score:+.1f}" if pr.ats_bonus_score is not None else "N/A"
            click.echo(f"  ATS Bonus: {pr.ats_bonus_team} → {ats_str}")
        click.echo()


if __name__ == "__main__":
    cli()
