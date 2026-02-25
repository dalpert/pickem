from __future__ import annotations

import base64
import html
from datetime import datetime
from pathlib import Path

from pickem.models import Game, PlayerResult
from pickem.season import SeasonData

AVATAR_DIR = Path(__file__).parent / "avatars"


def _load_avatars(names: list[str]) -> dict[str, str]:
    """Load avatar images as base64 data URIs.

    Looks for files named like 'adam.png', 'adam.jpg', etc. in the avatars dir.
    Returns {name: data_uri_string} for any found, empty string if not found.
    """
    avatars: dict[str, str] = {}
    for name in names:
        avatars[name] = ""
        if not AVATAR_DIR.exists():
            continue
        for ext in ("png", "jpg", "jpeg", "webp", "gif"):
            path = AVATAR_DIR / f"{name.lower()}.{ext}"
            if path.exists():
                mime = "image/png" if ext == "png" else f"image/{ext}"
                if ext == "jpg":
                    mime = "image/jpeg"
                data = base64.b64encode(path.read_bytes()).decode()
                avatars[name] = f"data:{mime};base64,{data}"
                break
    return avatars


def generate_report(
    season_data: SeasonData,
    all_week_results: dict[int, tuple[list[Game], list[PlayerResult]]],
    season: int,
) -> str:
    """Generate a self-contained HTML report."""
    standings = season_data.standings
    weeks = season_data.weeks_graded

    # Player colors (designed for light background)
    colors = [
        "#4a7c96", "#c0504d", "#3d8b5e", "#7b6b9e",
        "#c98442", "#5a9e9e", "#8b7d42", "#96506e",
    ]

    # Load player avatars
    player_names = [ps.name for ps in standings]
    avatars = _load_avatars(player_names)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pick'em Results</title>
<style>
{_css()}
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>Pick'em Results</h1>
    <p class="subtitle">{season}-{str(season+1)[-2:]} NFL Season &middot; Weeks {weeks[0]}-{weeks[-1]}</p>
    <p class="updated">Updated {datetime.now().strftime("%b %d, %Y")}</p>
  </header>

  <section id="chart">
    <h2>Most Wins</h2>
    <div class="chart-controls">
      <span id="weekLabel" class="week-label">Week {weeks[0]} of {weeks[-1]}</span>
      <div class="controls-right">
        <button id="btnPlayPause" class="ctrl-btn">&#9654; Play</button>
        <button id="btnReset" class="ctrl-btn">&#8634; Reset</button>
        <button id="btnSpeed" class="ctrl-btn">1x</button>
      </div>
    </div>
    <div class="chart-container">
      <div id="raceTrack"></div>
    </div>
  </section>

  <section id="standings">
    <h2>Season Standings</h2>
    {_standings_table(standings, colors, weeks, avatars)}
  </section>

  <section id="atsChart">
    <h2>ATS Bonus Race</h2>
    <div class="chart-controls">
      <span id="atsWeekLabel" class="week-label">Week {weeks[0]} of {weeks[-1]}</span>
      <div class="controls-right">
        <button id="atsBtnPlay" class="ctrl-btn">&#9654; Play</button>
        <button id="atsBtnReset" class="ctrl-btn">&#8634; Reset</button>
        <button id="atsBtnSpeed" class="ctrl-btn">1x</button>
      </div>
    </div>
    <div class="chart-container">
      <div id="atsRaceTrack"></div>
    </div>
  </section>

  <section id="ats">
    <h2>ATS Bonus Leaderboard</h2>
    {_ats_table(standings, colors, all_week_results, weeks, avatars)}
  </section>

  <section id="weeks">
    <h2>Week-by-Week Results</h2>
    {_week_sections(all_week_results, weeks)}
  </section>
</div>

<script>
{_chart_js(season_data, colors, avatars)}
{_ats_chart_js(season_data, colors, avatars)}
{_sort_js()}
{_expand_js()}
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

def _css() -> str:
    return """
:root {
  --bg: #f5f6f8;
  --surface: #ffffff;
  --surface2: #eef0f4;
  --text: #2d3748;
  --text-muted: #8892a4;
  --accent: #4a7c96;
  --green: #3d8b5e;
  --red: #c0504d;
  --border: #d8dce4;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
}
.container { max-width: 1100px; margin: 0 auto; padding: 2rem 1rem; }
header { text-align: center; margin-bottom: 3rem; }
h1 { font-size: 2.5rem; font-weight: 800; color: var(--accent); }
.subtitle { color: var(--text-muted); font-size: 1.1rem; margin-top: 0.25rem; }
.updated { color: var(--text-muted); font-size: 0.85rem; margin-top: 0.25rem; }
h2 {
  font-size: 1.5rem; font-weight: 700; margin-bottom: 1rem;
  padding-bottom: 0.5rem; border-bottom: 2px solid var(--accent);
}
section { margin-bottom: 3rem; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 0.6rem 0.8rem; text-align: left; }
th { color: var(--accent); font-weight: 600; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 2px solid var(--border); }
td { border-bottom: 1px solid var(--surface2); }
tr:hover td { background: var(--surface); }
.rank { font-weight: 700; color: var(--text-muted); width: 3rem; }
.name { font-weight: 600; }
.num { text-align: right; font-variant-numeric: tabular-nums; }
.pct { color: var(--accent); font-weight: 600; }
.positive { color: var(--green); }
.negative { color: var(--red); }
.correct { color: var(--green); }
.wrong { color: var(--red); }
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 0.5rem; vertical-align: middle; }

/* Player avatar */
.avatar {
  display: inline-block; width: 26px; height: 26px; border-radius: 50%;
  margin-right: 0.5rem; vertical-align: middle; object-fit: cover;
  border: 2px solid var(--border);
}
.avatar-placeholder {
  display: inline-flex; width: 26px; height: 26px; border-radius: 50%;
  margin-right: 0.5rem; vertical-align: middle;
  align-items: center; justify-content: center;
  font-size: 0.7rem; font-weight: 700; color: #fff;
  border: 2px solid var(--border);
}

/* Bar chart race */
.chart-container { background: var(--surface); border-radius: 12px; padding: 1.5rem; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
#raceTrack, #atsRaceTrack { position: relative; }
.race-bar {
  position: absolute; left: 0; right: 0; height: 40px;
  display: flex; align-items: center;
  transition: top 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}
.race-bar-fill {
  height: 32px; border-radius: 6px;
  display: flex; align-items: center; justify-content: flex-end;
  padding: 0 10px; min-width: 2px;
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}
.race-bar-value {
  color: #fff; font-weight: 700; font-size: 0.9rem;
  text-shadow: 0 1px 1px rgba(0,0,0,0.25);
  white-space: nowrap;
}
.race-bar-name {
  position: absolute; left: 0; top: 50%; transform: translateY(-50%);
  width: 100px; display: flex; align-items: center; gap: 6px;
  padding-left: 4px;
}
.race-bar-avatar {
  width: 32px; height: 32px; border-radius: 50%; object-fit: cover;
  border: 2px solid var(--border); flex-shrink: 0;
}
.race-bar-avatar-placeholder {
  width: 32px; height: 32px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.75rem; font-weight: 700; color: #fff;
  border: 2px solid var(--border); flex-shrink: 0;
}
.race-bar-label {
  font-weight: 700; font-size: 0.75rem; color: var(--text);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.race-bar-inner { margin-left: 108px; flex: 1; position: relative; }

/* ATS chart - negative value support */
.ats-bar-track { position: relative; height: 32px; margin-left: 108px; width: calc(100% - 108px); }
.ats-bar-zero {
  position: absolute; top: -4px; bottom: -4px; width: 2px;
  background: var(--text); opacity: 0.3; z-index: 2;
}
.ats-bar-fill {
  position: absolute; top: 0; height: 32px; border-radius: 6px;
  transition: left 0.5s cubic-bezier(0.4, 0, 0.2, 1),
              width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 2px;
}
.ats-val {
  position: absolute; top: 50%; transform: translateY(-50%);
  font-weight: 700; font-size: 0.85rem; white-space: nowrap;
  color: var(--text); z-index: 3;
}

/* Controls */
.chart-controls {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;
}
.week-label {
  font-size: 1.2rem; font-weight: 700; color: var(--accent); font-variant-numeric: tabular-nums;
}
.controls-right { display: flex; gap: 0.5rem; }
.ctrl-btn {
  background: var(--surface2); color: var(--text); border: 1px solid var(--border);
  border-radius: 6px; padding: 0.4rem 0.8rem; cursor: pointer;
  font-size: 0.85rem; font-weight: 600; transition: background 0.15s;
}
.ctrl-btn:hover { background: var(--border); }

/* Sortable headers */
.sortable { cursor: pointer; user-select: none; }
.sortable:hover { color: var(--text); }

/* Expandable table rows */
.expandable { cursor: pointer; }
.expandable td:first-child::before { content: '\\25B8 '; color: var(--text-muted); font-size: 0.7rem; }
.expandable.expanded td:first-child::before { content: '\\25BE '; }
.detail-row td { padding: 0; border-bottom: none; }
.detail-row:hover td { background: none; }
.detail-content {
  padding: 0.75rem 1rem 1rem; background: var(--bg);
  border-bottom: 2px solid var(--surface2); overflow-x: auto;
}

/* Week record grid (standings detail) */
.wr-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(65px, 1fr)); gap: 0.4rem;
}
.wr-cell {
  text-align: center; padding: 0.3rem; background: var(--surface2); border-radius: 4px;
}
.wr-week { display: block; font-size: 0.7rem; color: var(--text-muted); font-weight: 600; }
.wr-rec { display: block; font-size: 0.85rem; font-weight: 700; font-variant-numeric: tabular-nums; }

/* ATS detail inner table */
.ats-detail-table { width: 100%; font-size: 0.85rem; }
.ats-detail-table th { font-size: 0.75rem; padding: 0.3rem 0.5rem; }
.ats-detail-table td { padding: 0.3rem 0.5rem; border-bottom: 1px solid var(--surface2); }

/* Week-by-week cards */
details { background: var(--surface); border-radius: 8px; margin-bottom: 0.75rem; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
summary {
  padding: 0.8rem 1rem; cursor: pointer; font-weight: 600;
  display: flex; justify-content: space-between; align-items: center;
}
summary:hover { background: var(--surface2); border-radius: 8px; }
.week-content { padding: 0 1rem 1rem; }
.week-content table { font-size: 0.9rem; }
.pick-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem; margin-top: 1rem; }
.player-card { background: var(--surface2); border-radius: 8px; padding: 1rem; }
.player-card h4 { margin-bottom: 0.5rem; }
.pick-row { display: flex; justify-content: space-between; padding: 0.15rem 0; font-size: 0.85rem; }
.pick-icon { margin-right: 0.3rem; }

/* Winner celebration */
.celebrate-overlay {
  position: absolute; inset: 0; z-index: 10;
  display: flex; align-items: center; justify-content: center;
  pointer-events: none; opacity: 0;
  transition: opacity 0.6s ease;
}
.celebrate-overlay.show { opacity: 1; }
.celebrate-banner {
  background: var(--surface); border: 2px solid var(--accent);
  border-radius: 16px; padding: 1.25rem 2rem;
  box-shadow: 0 8px 32px rgba(0,0,0,0.12);
  display: flex; align-items: center; gap: 1rem;
  pointer-events: auto;
}
.celebrate-avatar {
  width: 52px; height: 52px; border-radius: 50%; object-fit: cover;
  border: 3px solid var(--accent);
}
.celebrate-avatar-placeholder {
  width: 52px; height: 52px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.4rem; font-weight: 800; color: #fff;
  border: 3px solid var(--accent);
}
.celebrate-text { text-align: left; }
.celebrate-name { font-size: 1.3rem; font-weight: 800; color: var(--accent); }
.celebrate-record { font-size: 0.9rem; color: var(--text-muted); font-weight: 600; }
.confetti-piece {
  position: absolute; width: 8px; height: 8px; border-radius: 2px;
  opacity: 0; z-index: 9;
}
@keyframes confetti-fall {
  0% { transform: translateY(0) rotate(0deg); opacity: 1; }
  100% { transform: translateY(280px) rotate(720deg); opacity: 0; }
}

@media (max-width: 700px) {
  h1 { font-size: 1.8rem; }
  th, td { padding: 0.4rem; font-size: 0.85rem; }
  .pick-grid { grid-template-columns: 1fr; }
  .chart-controls { flex-direction: column; gap: 0.5rem; }
  .controls-right { justify-content: center; }
}
"""


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def _build_ats_details(
    all_week_results: dict[int, tuple[list[Game], list[PlayerResult]]],
    weeks: list[int],
) -> dict[str, list[tuple[int, str, str, str, str, float]]]:
    """Build per-player week-by-week ATS detail rows.

    Returns {player_name: [(week, team, matchup, score_str, spread_str, ats_score), ...]}
    """
    details: dict[str, list[tuple[int, str, str, str, str, float]]] = {}

    for week in weeks:
        if week not in all_week_results:
            continue
        games, results = all_week_results[week]

        # Build game score lookup from first player who has details
        game_scores: dict[tuple[str, str], tuple[int, int]] = {}
        for pr in results:
            for d in pr.details:
                key = (d.game.away_team, d.game.home_team)
                if key not in game_scores:
                    game_scores[key] = (d.away_score, d.home_score)

        for pr in results:
            if not pr.ats_bonus_team or pr.ats_bonus_score is None:
                continue

            # Find which game this ATS team belongs to
            ats_game = None
            picked_away = False
            for g in games:
                if pr.ats_bonus_team == g.away_team:
                    ats_game = g
                    picked_away = True
                    break
                elif pr.ats_bonus_team == g.home_team:
                    ats_game = g
                    picked_away = False
                    break

            if ats_game is None:
                continue

            opponent = ats_game.home_team if picked_away else ats_game.away_team
            matchup = f"@ {opponent}" if picked_away else f"vs {opponent}"

            scores = game_scores.get((ats_game.away_team, ats_game.home_team))
            score_str = f"{scores[0]}-{scores[1]}" if scores else "N/A"

            spread_val = ats_game.spread if picked_away else -ats_game.spread
            spread_str = f"{spread_val:+.1f}"

            if pr.name not in details:
                details[pr.name] = []
            details[pr.name].append((
                week, pr.ats_bonus_team, matchup, score_str,
                spread_str, pr.ats_bonus_score,
            ))

    return details


def _avatar_html(name: str, color: str, avatars: dict[str, str]) -> str:
    """Return an <img> avatar tag or a colored placeholder circle."""
    data_uri = avatars.get(name, "")
    if data_uri:
        return f'<img class="avatar" src="{data_uri}" alt="{_esc(name)}">'
    initial = name[0].upper() if name else "?"
    return f'<span class="avatar-placeholder" style="background:{color}">{initial}</span>'


# ---------------------------------------------------------------------------
# HTML tables
# ---------------------------------------------------------------------------

def _standings_table(standings, colors, weeks, avatars) -> str:
    rows = ""
    for i, ps in enumerate(standings):
        color = colors[i % len(colors)]
        pct = f"{ps.win_pct:.1%}"
        avatar = _avatar_html(ps.name, color, avatars)
        rows += f"""<tr class="expandable" data-idx="{i}">
  <td class="rank">{i+1}</td>
  <td class="name">{avatar}{_esc(ps.name)}</td>
  <td class="num" data-val="{ps.total_correct}">{ps.total_correct}</td>
  <td class="num" data-val="{ps.total_losses}">{ps.total_losses}</td>
  <td class="num pct" data-val="{ps.win_pct:.4f}">{pct}</td>
</tr>"""
        # Detail row with week-by-week records
        cells = ""
        for week in weeks:
            record = ps.weekly_records.get(week)
            if record:
                w, l, p = record
                rec = f"{w}-{l}"
                if p > 0:
                    rec += f"-{p}"
            else:
                rec = "-"
            cells += f'<div class="wr-cell"><span class="wr-week">W{week}</span><span class="wr-rec">{rec}</span></div>'
        rows += f"""<tr class="detail-row" data-idx="{i}" style="display:none">
  <td colspan="5"><div class="detail-content"><div class="wr-grid">{cells}</div></div></td>
</tr>"""

    return f"""<table id="standingsTable">
<thead><tr><th class="rank">#</th><th>Name</th><th class="num sortable" data-col="2">W &#9660;</th><th class="num sortable" data-col="3">L</th><th class="num sortable" data-col="4">Pct</th></tr></thead>
<tbody>{rows}</tbody>
</table>"""


def _ats_table(standings, colors, all_week_results, weeks, avatars) -> str:
    by_ats = sorted(standings, key=lambda p: p.total_ats_bonus, reverse=True)
    ats_details = _build_ats_details(all_week_results, weeks)

    rows = ""
    for i, ps in enumerate(by_ats):
        color = colors[standings.index(ps) % len(colors)]
        cls = "positive" if ps.total_ats_bonus >= 0 else "negative"
        avatar = _avatar_html(ps.name, color, avatars)

        rows += f"""<tr class="expandable" data-idx="ats{i}">
  <td class="rank">{i+1}</td>
  <td class="name">{avatar}{_esc(ps.name)}</td>
  <td class="num {cls}">{ps.total_ats_bonus:+.1f}</td>
</tr>"""

        # Detail rows: per-week ATS breakdown
        player_details = ats_details.get(ps.name, [])
        detail_rows = ""
        for week, team, matchup, score_str, spread_str, ats_score in player_details:
            bcls = "positive" if ats_score >= 0 else "negative"
            detail_rows += f"""<tr>
  <td>{week}</td><td>{_esc(team)}</td><td>{_esc(matchup)}</td>
  <td>{score_str}</td><td>{spread_str}</td><td class="num {bcls}">{ats_score:+.1f}</td>
</tr>"""

        rows += f"""<tr class="detail-row" data-idx="ats{i}" style="display:none">
  <td colspan="3"><div class="detail-content">
    <table class="ats-detail-table">
      <thead><tr><th>Wk</th><th>Team</th><th>Matchup</th><th>Score</th><th>Spread</th><th class="num">Bonus</th></tr></thead>
      <tbody>{detail_rows}</tbody>
    </table>
  </div></td>
</tr>"""

    return f"""<table id="atsTable">
<thead><tr><th class="rank">#</th><th>Name</th><th class="num">ATS Total</th></tr></thead>
<tbody>{rows}</tbody>
</table>"""


def _week_sections(
    all_week_results: dict[int, tuple[list[Game], list[PlayerResult]]],
    weeks: list[int],
) -> str:
    sections = ""
    for week in reversed(weeks):  # Most recent first
        if week not in all_week_results:
            continue
        games, results = all_week_results[week]
        winner = results[0] if results else None
        summary_text = f"Week {week}"
        winner_text = f"{winner.name}: {winner.correct}-{winner.losses}" if winner else ""

        # Build player cards
        cards = ""
        for pr in results:
            picks_html = ""
            for detail in pr.details:
                if detail.push:
                    icon = '<span class="pick-icon" style="color:var(--text-muted)">&#8860;</span>'
                elif detail.correct:
                    icon = '<span class="pick-icon correct">&#10003;</span>'
                else:
                    icon = '<span class="pick-icon wrong">&#10007;</span>'
                score = f"{detail.away_score}-{detail.home_score}"
                # Show the spread from the picked team's perspective
                if detail.push:
                    spread_str = " (PUSH)"
                elif detail.picked_away:
                    spread_str = f" ({detail.game.spread:+.1f})"
                else:
                    spread_str = f" ({-detail.game.spread:+.1f})"
                picks_html += f'<div class="pick-row">{icon}{_esc(detail.picked)}{spread_str}<span class="num">{score}</span></div>'

            ats_html = ""
            if pr.ats_bonus_team:
                cls = "positive" if (pr.ats_bonus_score or 0) >= 0 else "negative"
                ats_val = f"{pr.ats_bonus_score:+.1f}" if pr.ats_bonus_score is not None else "N/A"
                ats_html = f'<div class="pick-row" style="margin-top:0.5rem;font-weight:600">ATS: {_esc(pr.ats_bonus_team)} <span class="{cls}">{ats_val}</span></div>'

            record_str = f"{pr.correct}-{pr.losses}"
            if pr.pushes > 0:
                record_str += f"-{pr.pushes}"
            cards += f"""<div class="player-card">
  <h4>{_esc(pr.name)}: {record_str}</h4>
  {picks_html}
  {ats_html}
</div>"""

        sections += f"""<details>
  <summary><span>{summary_text}</span><span style="color:var(--text-muted)">{winner_text}</span></summary>
  <div class="week-content">
    <div class="pick-grid">{cards}</div>
  </div>
</details>"""

    return sections


# ---------------------------------------------------------------------------
# JavaScript — Win Race bar chart
# ---------------------------------------------------------------------------

def _chart_js(season_data: SeasonData, colors: list[str], avatars: dict[str, str]) -> str:
    """Generate JS for animated bar chart race (wins) with winner celebration."""
    standings = season_data.standings
    weeks = season_data.weeks_graded

    player_entries = []
    for i, ps in enumerate(standings):
        color = colors[i % len(colors)]
        cumulative = []
        total = 0
        for week in weeks:
            record = ps.weekly_records.get(week)
            if record:
                total += record[0]
            cumulative.append(total)
        values_str = ", ".join(str(v) for v in cumulative)
        avatar_uri = avatars.get(ps.name, "")
        player_entries.append(
            f"{{ name: '{_esc_js(ps.name)}', color: '{color}', values: [{values_str}], avatar: '{avatar_uri}' }}"
        )

    all_data_str = ",\n  ".join(player_entries)
    labels_str = ", ".join(f"'W{w}'" for w in weeks)

    return f"""
const allLabels = [{labels_str}];
const allData = [
  {all_data_str}
];
const totalWeeks = allLabels.length;
const BAR_H = 48;
const track = document.getElementById('raceTrack');
const chartContainer = track.parentElement;
chartContainer.style.position = 'relative';

let xMax = 0;
allData.forEach(d => {{ d.values.forEach(v => {{ if (v > xMax) xMax = v; }}); }});
xMax = Math.ceil(xMax / 5) * 5 + 5;

const bars = allData.map((d, i) => {{
  const row = document.createElement('div');
  row.className = 'race-bar';
  row.style.top = (i * BAR_H) + 'px';
  var avatarTag;
  if (d.avatar) {{
    avatarTag = '<img class="race-bar-avatar" src="' + d.avatar + '" alt="' + d.name + '">';
  }} else {{
    avatarTag = '<span class="race-bar-avatar-placeholder" style="background:' + d.color + '">' + d.name[0] + '</span>';
  }}
  row.innerHTML = '<span class="race-bar-name">' + avatarTag + '<span class="race-bar-label">' + d.name + '</span></span>' +
    '<div class="race-bar-inner">' +
      '<div class="race-bar-fill" style="background:' + d.color + ';width:0%">' +
        '<span class="race-bar-value">0</span>' +
      '</div>' +
    '</div>';
  track.appendChild(row);
  return {{ el: row, fill: row.querySelector('.race-bar-fill'), valEl: row.querySelector('.race-bar-value'), idx: i }};
}});
track.style.height = (allData.length * BAR_H) + 'px';

// Create celebration overlay
const celebOverlay = document.createElement('div');
celebOverlay.className = 'celebrate-overlay';
chartContainer.appendChild(celebOverlay);

function celebrate() {{
  // Find the winner (highest final value)
  let winnerIdx = 0, winnerVal = 0;
  allData.forEach((d, i) => {{
    const v = d.values[totalWeeks - 1];
    if (v > winnerVal) {{ winnerVal = v; winnerIdx = i; }}
  }});
  const winner = allData[winnerIdx];
  const losses = {standings[0].total_games} - winnerVal;

  // Build banner
  var avatarHtml;
  if (winner.avatar) {{
    avatarHtml = '<img class="celebrate-avatar" src="' + winner.avatar + '" alt="' + winner.name + '">';
  }} else {{
    avatarHtml = '<span class="celebrate-avatar-placeholder" style="background:' + winner.color + '">' + winner.name[0] + '</span>';
  }}
  celebOverlay.innerHTML =
    '<div class="celebrate-banner">' +
      avatarHtml +
      '<div class="celebrate-text">' +
        '<div class="celebrate-name">' + winner.name + ' wins!</div>' +
        '<div class="celebrate-record">' + winnerVal + '-' + losses + '</div>' +
      '</div>' +
    '</div>';

  // Confetti burst
  const confettiColors = ['#4a7c96', '#c0504d', '#3d8b5e', '#7b6b9e', '#c98442', '#5a9e9e', '#d4af37', '#96506e'];
  const rect = chartContainer.getBoundingClientRect();
  for (var i = 0; i < 60; i++) {{
    var piece = document.createElement('div');
    piece.className = 'confetti-piece';
    piece.style.background = confettiColors[Math.floor(Math.random() * confettiColors.length)];
    piece.style.left = (10 + Math.random() * 80) + '%';
    piece.style.top = (Math.random() * 30) + '%';
    piece.style.width = (6 + Math.random() * 6) + 'px';
    piece.style.height = (6 + Math.random() * 6) + 'px';
    piece.style.borderRadius = Math.random() > 0.5 ? '50%' : '2px';
    piece.style.animation = 'confetti-fall ' + (1.2 + Math.random() * 1.5) + 's ease-out ' + (Math.random() * 0.5) + 's forwards';
    chartContainer.appendChild(piece);
  }}

  setTimeout(() => {{ celebOverlay.classList.add('show'); }}, 200);
}}

function clearCelebration() {{
  celebOverlay.classList.remove('show');
  celebOverlay.innerHTML = '';
  chartContainer.querySelectorAll('.confetti-piece').forEach(p => p.remove());
}}

let currentWeek = 0, intervalId = null, speed = 1500;
const SPEEDS = [1500, 750, 375], SPEED_LABELS = ['1x', '2x', '4x'];
let speedIdx = 0;
const weekLabel = document.getElementById('weekLabel');
const btnPlay = document.getElementById('btnPlayPause');
const btnReset = document.getElementById('btnReset');
const btnSpeed = document.getElementById('btnSpeed');

function renderWeek(wi) {{
  const snap = allData.map((d, i) => ({{ idx: i, val: d.values[wi] }}));
  snap.sort((a, b) => b.val - a.val);
  const rank = {{}};
  snap.forEach((s, r) => {{ rank[s.idx] = r; }});
  bars.forEach(b => {{
    const v = allData[b.idx].values[wi];
    b.fill.style.width = (xMax > 0 ? (v / xMax) * 100 : 0) + '%';
    b.valEl.textContent = v;
    b.el.style.top = (rank[b.idx] * BAR_H) + 'px';
  }});
  weekLabel.textContent = 'Week ' + allLabels[wi].replace('W','') + ' of ' + totalWeeks;
}}

function advance() {{
  if (currentWeek >= totalWeeks - 1) {{ stopAnim(); btnPlay.innerHTML = '&#9654; Replay'; celebrate(); return; }}
  currentWeek++; renderWeek(currentWeek);
}}
function playAnim() {{
  if (currentWeek >= totalWeeks - 1) {{ resetAnim(); }}
  clearCelebration();
  intervalId = setInterval(advance, speed);
  btnPlay.innerHTML = '&#9646;&#9646; Pause';
}}
function stopAnim() {{ clearInterval(intervalId); intervalId = null; if (currentWeek < totalWeeks - 1) btnPlay.innerHTML = '&#9654; Play'; }}
function resetAnim() {{
  stopAnim(); currentWeek = 0; clearCelebration();
  bars.forEach(b => {{ b.el.style.transition = 'none'; b.fill.style.transition = 'none'; }});
  renderWeek(0); track.offsetHeight;
  bars.forEach(b => {{ b.el.style.transition = ''; b.fill.style.transition = ''; }});
  btnPlay.innerHTML = '&#9654; Play';
}}

btnPlay.addEventListener('click', () => {{ if (intervalId) stopAnim(); else playAnim(); }});
btnReset.addEventListener('click', resetAnim);
btnSpeed.addEventListener('click', () => {{
  speedIdx = (speedIdx + 1) % SPEEDS.length; speed = SPEEDS[speedIdx];
  btnSpeed.textContent = SPEED_LABELS[speedIdx];
  if (intervalId) {{ stopAnim(); playAnim(); }}
}});

const obs1 = new IntersectionObserver(e => {{
  if (e[0].isIntersecting && !intervalId && currentWeek === 0) {{ playAnim(); obs1.disconnect(); }}
}}, {{ threshold: 0.3 }});
obs1.observe(document.getElementById('chart'));
renderWeek(0);"""


# ---------------------------------------------------------------------------
# JavaScript — ATS Bonus Race bar chart
# ---------------------------------------------------------------------------

def _ats_chart_js(season_data: SeasonData, colors: list[str], avatars: dict[str, str]) -> str:
    """Generate JS for animated ATS bar chart race (supports negatives) with winner celebration."""
    standings = season_data.standings
    weeks = season_data.weeks_graded

    player_entries = []
    for i, ps in enumerate(standings):
        color = colors[i % len(colors)]
        cumulative = []
        total = 0.0
        for week in weeks:
            ats = ps.weekly_ats.get(week)
            if ats is not None:
                total += ats
            cumulative.append(round(total, 1))
        values_str = ", ".join(str(v) for v in cumulative)
        avatar_uri = avatars.get(ps.name, "")
        player_entries.append(
            f"{{ name: '{_esc_js(ps.name)}', color: '{color}', values: [{values_str}], avatar: '{avatar_uri}' }}"
        )

    all_data_str = ",\n  ".join(player_entries)
    labels_str = ", ".join(f"'W{w}'" for w in weeks)

    return f"""
const atsLabels = [{labels_str}];
const atsData = [
  {all_data_str}
];
const atsTotalWeeks = atsLabels.length;
const ATS_BAR_H = 48;
const atsTrack = document.getElementById('atsRaceTrack');
const atsChartContainer = atsTrack.parentElement;
atsChartContainer.style.position = 'relative';

// Create celebration overlay for ATS chart
const atsCelebOverlay = document.createElement('div');
atsCelebOverlay.className = 'celebrate-overlay';
atsChartContainer.appendChild(atsCelebOverlay);

// Compute symmetric scale so zero is centered
let atsAbsMax = 0;
atsData.forEach(d => {{ d.values.forEach(v => {{ var a = Math.abs(v); if (a > atsAbsMax) atsAbsMax = a; }}); }});
atsAbsMax = Math.ceil(atsAbsMax / 10) * 10 + 10;
const atsMin = -atsAbsMax;
const atsMax = atsAbsMax;
const atsRange = atsMax - atsMin;
const zeroPct = 50; // zero is always centered

// Create bar elements
const atsBars = atsData.map((d, i) => {{
  const row = document.createElement('div');
  row.className = 'race-bar';
  row.style.top = (i * ATS_BAR_H) + 'px';
  var avatarTag;
  if (d.avatar) {{
    avatarTag = '<img class="race-bar-avatar" src="' + d.avatar + '" alt="' + d.name + '">';
  }} else {{
    avatarTag = '<span class="race-bar-avatar-placeholder" style="background:' + d.color + '">' + d.name[0] + '</span>';
  }}
  row.innerHTML = '<span class="race-bar-name">' + avatarTag + '<span class="race-bar-label">' + d.name + '</span></span>' +
    '<div class="ats-bar-track">' +
      '<div class="ats-bar-zero" style="left:' + zeroPct + '%"></div>' +
      '<div class="ats-bar-fill" style="background:' + d.color + ';left:' + zeroPct + '%;width:0%"></div>' +
      '<span class="ats-val" style="left:' + zeroPct + '%;top:50%;transform:translateY(-50%)">0.0</span>' +
    '</div>';
  atsTrack.appendChild(row);
  return {{
    el: row,
    fill: row.querySelector('.ats-bar-fill'),
    valEl: row.querySelector('.ats-val'),
    idx: i,
  }};
}});
atsTrack.style.height = (atsData.length * ATS_BAR_H) + 'px';

let atsCurWeek = 0, atsIntId = null, atsSpeed = 1500;
const ATS_SPEEDS = [1500, 750, 375], ATS_SPEED_LBL = ['1x', '2x', '4x'];
let atsSpeedIdx = 0;
const atsWeekLabel = document.getElementById('atsWeekLabel');
const atsBtnPlay = document.getElementById('atsBtnPlay');
const atsBtnReset = document.getElementById('atsBtnReset');
const atsBtnSpeed = document.getElementById('atsBtnSpeed');

function renderAtsWeek(wi) {{
  const snap = atsData.map((d, i) => ({{ idx: i, val: d.values[wi] }}));
  snap.sort((a, b) => b.val - a.val);
  const rank = {{}};
  snap.forEach((s, r) => {{ rank[s.idx] = r; }});

  atsBars.forEach(b => {{
    const v = atsData[b.idx].values[wi];
    // Percentage position of this value within [atsMin, atsMax]
    const valPct = ((v - atsMin) / atsRange) * 100;
    const barWidthPct = Math.abs(valPct - zeroPct);

    if (v >= 0) {{
      b.fill.style.left = zeroPct + '%';
      b.fill.style.width = Math.max(barWidthPct, 0.3) + '%';
      b.fill.style.borderRadius = '0 6px 6px 0';
      // Label to the right of the bar end
      b.valEl.style.left = (zeroPct + barWidthPct) + '%';
      b.valEl.style.transform = 'translateY(-50%)';
      b.valEl.style.marginLeft = '6px';
      b.valEl.style.marginRight = '';
    }} else {{
      b.fill.style.left = valPct + '%';
      b.fill.style.width = Math.max(barWidthPct, 0.3) + '%';
      b.fill.style.borderRadius = '6px 0 0 6px';
      // Label to the left of the bar start
      b.valEl.style.left = valPct + '%';
      b.valEl.style.transform = 'translateY(-50%) translateX(-100%)';
      b.valEl.style.marginLeft = '';
      b.valEl.style.marginRight = '6px';
    }}
    b.valEl.textContent = (v >= 0 ? '+' : '') + v.toFixed(1);
    b.valEl.style.top = '50%';
    b.el.style.top = (rank[b.idx] * ATS_BAR_H) + 'px';
  }});
  atsWeekLabel.textContent = 'Week ' + atsLabels[wi].replace('W','') + ' of ' + atsTotalWeeks;
}}

function celebrateAts() {{
  // Find the winner (highest final ATS value)
  let winnerIdx = 0, winnerVal = -999999;
  atsData.forEach((d, i) => {{
    const v = d.values[atsTotalWeeks - 1];
    if (v > winnerVal) {{ winnerVal = v; winnerIdx = i; }}
  }});
  const winner = atsData[winnerIdx];

  // Build banner
  var avatarHtml;
  if (winner.avatar) {{
    avatarHtml = '<img class="celebrate-avatar" src="' + winner.avatar + '" alt="' + winner.name + '">';
  }} else {{
    avatarHtml = '<span class="celebrate-avatar-placeholder" style="background:' + winner.color + '">' + winner.name[0] + '</span>';
  }}
  atsCelebOverlay.innerHTML =
    '<div class="celebrate-banner">' +
      avatarHtml +
      '<div class="celebrate-text">' +
        '<div class="celebrate-name">' + winner.name + ' wins!</div>' +
        '<div class="celebrate-record">ATS: ' + (winnerVal >= 0 ? '+' : '') + winnerVal.toFixed(1) + '</div>' +
      '</div>' +
    '</div>';

  // Confetti burst
  const confettiColors = ['#4a7c96', '#c0504d', '#3d8b5e', '#7b6b9e', '#c98442', '#5a9e9e', '#d4af37', '#96506e'];
  for (var i = 0; i < 60; i++) {{
    var piece = document.createElement('div');
    piece.className = 'confetti-piece';
    piece.style.background = confettiColors[Math.floor(Math.random() * confettiColors.length)];
    piece.style.left = (10 + Math.random() * 80) + '%';
    piece.style.top = (Math.random() * 30) + '%';
    piece.style.width = (6 + Math.random() * 6) + 'px';
    piece.style.height = (6 + Math.random() * 6) + 'px';
    piece.style.borderRadius = Math.random() > 0.5 ? '50%' : '2px';
    piece.style.animation = 'confetti-fall ' + (1.2 + Math.random() * 1.5) + 's ease-out ' + (Math.random() * 0.5) + 's forwards';
    atsChartContainer.appendChild(piece);
  }}

  setTimeout(() => {{ atsCelebOverlay.classList.add('show'); }}, 200);
}}

function clearAtsCelebration() {{
  atsCelebOverlay.classList.remove('show');
  atsCelebOverlay.innerHTML = '';
  atsChartContainer.querySelectorAll('.confetti-piece').forEach(p => p.remove());
}}

function atsAdvance() {{
  if (atsCurWeek >= atsTotalWeeks - 1) {{ atsStop(); atsBtnPlay.innerHTML = '&#9654; Replay'; celebrateAts(); return; }}
  atsCurWeek++; renderAtsWeek(atsCurWeek);
}}
function atsPlay() {{
  if (atsCurWeek >= atsTotalWeeks - 1) {{ atsReset(); }}
  clearAtsCelebration();
  atsIntId = setInterval(atsAdvance, atsSpeed);
  atsBtnPlay.innerHTML = '&#9646;&#9646; Pause';
}}
function atsStop() {{ clearInterval(atsIntId); atsIntId = null; if (atsCurWeek < atsTotalWeeks - 1) atsBtnPlay.innerHTML = '&#9654; Play'; }}
function atsReset() {{
  atsStop(); atsCurWeek = 0; clearAtsCelebration();
  atsBars.forEach(b => {{ b.el.style.transition = 'none'; b.fill.style.transition = 'none'; }});
  renderAtsWeek(0); atsTrack.offsetHeight;
  atsBars.forEach(b => {{ b.el.style.transition = ''; b.fill.style.transition = ''; }});
  atsBtnPlay.innerHTML = '&#9654; Play';
}}

atsBtnPlay.addEventListener('click', () => {{ if (atsIntId) atsStop(); else atsPlay(); }});
atsBtnReset.addEventListener('click', atsReset);
atsBtnSpeed.addEventListener('click', () => {{
  atsSpeedIdx = (atsSpeedIdx + 1) % ATS_SPEEDS.length; atsSpeed = ATS_SPEEDS[atsSpeedIdx];
  atsBtnSpeed.textContent = ATS_SPEED_LBL[atsSpeedIdx];
  if (atsIntId) {{ atsStop(); atsPlay(); }}
}});

const obs2 = new IntersectionObserver(e => {{
  if (e[0].isIntersecting && !atsIntId && atsCurWeek === 0) {{ atsPlay(); obs2.disconnect(); }}
}}, {{ threshold: 0.3 }});
obs2.observe(document.getElementById('atsChart'));
renderAtsWeek(0);"""


# ---------------------------------------------------------------------------
# JavaScript — Sort & Expand
# ---------------------------------------------------------------------------

def _sort_js() -> str:
    """Generate JS for sortable standings table (works with expandable rows)."""
    return """
(function() {
  const table = document.getElementById('standingsTable');
  if (!table) return;
  const headers = table.querySelectorAll('th.sortable');
  let currentCol = 2;
  let currentDesc = true;

  function sortTable(colIdx, desc) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr.expandable'));
    rows.sort((a, b) => {
      const aVal = parseFloat(a.cells[colIdx].getAttribute('data-val'));
      const bVal = parseFloat(b.cells[colIdx].getAttribute('data-val'));
      return desc ? bVal - aVal : aVal - bVal;
    });
    // Collapse all expanded rows
    tbody.querySelectorAll('tr.detail-row').forEach(r => { r.style.display = 'none'; });
    tbody.querySelectorAll('tr.expandable.expanded').forEach(r => { r.classList.remove('expanded'); });
    // Re-rank and re-append with paired detail rows
    rows.forEach((row, i) => {
      row.cells[0].textContent = (i + 1);
      tbody.appendChild(row);
      const idx = row.getAttribute('data-idx');
      const detail = tbody.querySelector('tr.detail-row[data-idx="' + idx + '"]');
      if (detail) tbody.appendChild(detail);
    });
    // Update arrows
    headers.forEach(h => {
      const col = parseInt(h.getAttribute('data-col'));
      const label = h.textContent.replace(/ [\\u25B2\\u25BC]/g, '').trim();
      if (col === colIdx) {
        h.innerHTML = label + (desc ? ' \\u25BC' : ' \\u25B2');
      } else {
        h.textContent = label;
      }
    });
  }

  headers.forEach(h => {
    h.addEventListener('click', () => {
      const col = parseInt(h.getAttribute('data-col'));
      if (col === currentCol) {
        currentDesc = !currentDesc;
      } else {
        currentCol = col;
        currentDesc = true;
      }
      sortTable(currentCol, currentDesc);
    });
  });
})();"""


def _expand_js() -> str:
    """Generate JS for click-to-expand table rows."""
    return """
(function() {
  document.querySelectorAll('.expandable').forEach(function(row) {
    row.addEventListener('click', function() {
      var detail = this.nextElementSibling;
      if (detail && detail.classList.contains('detail-row')) {
        var isVisible = detail.style.display === 'table-row';
        detail.style.display = isVisible ? 'none' : 'table-row';
        this.classList.toggle('expanded');
      }
    });
  });
})();"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _esc(text: str) -> str:
    return html.escape(text)


def _esc_js(text: str) -> str:
    return text.replace("'", "\\'").replace("\n", "")
