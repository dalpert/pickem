# Pickem

NFL Pick'em pool grader. Pulls responses from a Google Form (via Google Sheets), fetches actual NFL scores from ESPN, and produces a ranked leaderboard.

## Setup

### 1. Install

```bash
cd pickem
pip install -e .
```

### 2. Google Cloud Service Account

You need a Google Cloud service account to read your Google Sheet.

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use an existing one)
3. Enable the **Google Sheets API**:
   - Navigate to **APIs & Services > Library**
   - Search for "Google Sheets API" and click **Enable**
4. Create a service account:
   - Go to **APIs & Services > Credentials**
   - Click **Create Credentials > Service Account**
   - Give it a name (e.g., "pickem-reader") and click through
5. Create a key:
   - Click into your new service account
   - Go to the **Keys** tab
   - Click **Add Key > Create new key > JSON**
   - Save the downloaded JSON file somewhere safe
6. Share your Google Sheet with the service account:
   - Open the JSON file and find the `client_email` field (looks like `pickem-reader@your-project.iam.gserviceaccount.com`)
   - Open your Google Sheet, click **Share**, and add that email as a viewer

### 3. Configure

Create a `.env` file in the project root (or set the env var directly):

```bash
cp .env.example .env
# Edit .env and set the path to your service account JSON
GOOGLE_SERVICE_ACCOUNT_KEY=/path/to/your/service-account-key.json
```

## Usage

### List available tabs

```bash
pickem tabs --sheet-url "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
```

### Grade a week

```bash
pickem grade \
  --sheet-url "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit" \
  --tab "Week 11" \
  --week 11
```

The season defaults to the current NFL season. Override with `--season 2025`.

### Options

- `--leaderboard-only` — skip per-player detail, just show the ranking
- `--no-cache` — re-fetch scores from ESPN (by default, scores are cached locally)

## How Scoring Works

- **Straight-up picks**: 1 point per correct winner (spreads are ignored for scoring)
- **ATS Bonus**: Each player picks one game as their ATS bonus. The bonus score = the picked team's margin of victory minus the spread. Used as a tiebreaker for weekly rankings and summed across the season for a season-long prize.
- **Ranking**: Players are ranked by wins (descending), then ATS bonus (descending) as tiebreaker.

## Form Format

The tool expects Google Form responses with columns like:

| Timestamp | Email Address | Name | Jets (+12.5) @ Patriots [TNF] | Commanders (+2.5) @ Dolphins | ... | ATS Bonus | Season Performance |
|-----------|--------------|------|-------------------------------|------------------------------|-----|-----------|-------------------|

Game columns follow the pattern: `Team (+/-spread) @ Team [optional tag]`
