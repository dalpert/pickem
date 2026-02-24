from __future__ import annotations

import os
import re
from pathlib import Path

import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/forms.body.readonly",
    "https://www.googleapis.com/auth/forms.responses.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


def _get_credentials() -> Credentials:
    """Load service account credentials."""
    key_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY")
    if not key_path:
        raise RuntimeError(
            "GOOGLE_SERVICE_ACCOUNT_KEY env var not set. "
            "Point it at your service account JSON file."
        )
    key_path = Path(key_path).expanduser()
    if not key_path.exists():
        raise FileNotFoundError(f"Service account key not found: {key_path}")
    return Credentials.from_service_account_file(str(key_path), scopes=SCOPES)


def _get_client() -> gspread.Client:
    return gspread.authorize(_get_credentials())


def extract_sheet_id(url_or_id: str) -> str:
    """Extract the spreadsheet ID from a URL or return as-is if already an ID."""
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", url_or_id)
    if match:
        return match.group(1)
    return url_or_id


def fetch_responses(sheet_id: str, tab_name: str) -> tuple[list[str], list[list[str]]]:
    """Fetch form responses from a Google Sheet tab.

    Returns (headers, rows) where headers is the first row and rows is everything else.
    """
    client = _get_client()
    spreadsheet = client.open_by_key(sheet_id)
    worksheet = spreadsheet.worksheet(tab_name)
    all_values = worksheet.get_all_values()
    if not all_values:
        raise ValueError(f"Tab '{tab_name}' is empty")
    headers = all_values[0]
    rows = all_values[1:]
    return headers, rows


def list_tabs(sheet_id: str) -> list[str]:
    """List all tab names in the spreadsheet."""
    client = _get_client()
    spreadsheet = client.open_by_key(sheet_id)
    return [ws.title for ws in spreadsheet.worksheets()]


def write_to_tab(
    sheet_id: str, tab_name: str, headers: list[str], rows: list[list[str]]
) -> None:
    """Write data to a tab in the spreadsheet.

    Creates the tab if it doesn't exist, or clears and overwrites if it does.
    """
    client = _get_client()
    spreadsheet = client.open_by_key(sheet_id)

    # Try to get existing tab, or create new one
    try:
        worksheet = spreadsheet.worksheet(tab_name)
        worksheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=tab_name, rows=len(rows) + 1, cols=len(headers)
        )

    # Write all data in one batch
    all_data = [headers] + rows
    worksheet.update(all_data, value_input_option="RAW")
