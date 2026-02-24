from __future__ import annotations

import re

from googleapiclient.discovery import build

from pickem.names import canonical_name
from pickem.sheets import _get_credentials


def _get_forms_service():
    creds = _get_credentials()
    return build("forms", "v1", credentials=creds)


def _get_drive_service():
    creds = _get_credentials()
    return build("drive", "v3", credentials=creds)


def extract_form_id(url_or_id: str) -> str:
    """Extract the form ID from a URL or return as-is."""
    match = re.search(r"/forms/d/([a-zA-Z0-9_-]+)", url_or_id)
    if match:
        return match.group(1)
    return url_or_id


def find_form_by_title(title: str) -> dict | None:
    """Search Google Drive for a form matching the exact title.

    Returns {id, name} or None.
    """
    drive = _get_drive_service()
    query = (
        f"mimeType='application/vnd.google-apps.form' "
        f"and name='{title}' "
        f"and trashed=false"
    )
    result = drive.files().list(
        q=query, spaces="drive", fields="files(id, name)", pageSize=10
    ).execute()
    files = result.get("files", [])
    return files[0] if files else None


def find_pickem_form(week: int) -> dict | None:
    """Find the pick'em form for a given week.

    Searches for 'Week {week}: Boyz and jordan pick em [25-26]'.
    """
    title = f"Week {week}: Boyz and jordan pick em [25-26]"
    return find_form_by_title(title)


def get_form_structure(form_id: str) -> dict:
    """Get the full form structure including question titles and IDs."""
    service = _get_forms_service()
    return service.forms().get(formId=form_id).execute()


def get_form_responses(form_id: str) -> list[dict]:
    """Get all responses for a form."""
    service = _get_forms_service()
    result = service.forms().responses().list(formId=form_id).execute()
    return result.get("responses", [])


def export_form_to_rows(
    form_id: str,
) -> tuple[list[str], list[list[str]]]:
    """Read a form's structure and responses, returning (headers, rows).

    The output format matches what Google Forms auto-generates in Sheets:
    Timestamp | Email Address | Name | <game columns> | ATS Bonus | <extra questions>
    """
    form = get_form_structure(form_id)
    responses = get_form_responses(form_id)

    # Build ordered list of questions: (question_id, title)
    questions: list[tuple[str, str]] = []
    for item in form.get("items", []):
        q_item = item.get("questionItem")
        if q_item is None:
            continue
        q_id = q_item["question"]["questionId"]
        title = item.get("title", "")
        questions.append((q_id, title))

    # Headers: Timestamp, Email Address, then question titles
    headers = ["Timestamp", "Email Address"] + [title for _, title in questions]

    # Find the Name question ID so we can use it for fallback name
    name_qid = None
    for q_id, title in questions:
        if title.lower() == "name":
            name_qid = q_id
            break

    # Build rows from responses
    rows: list[list[str]] = []
    for resp in responses:
        timestamp = resp.get("lastSubmittedTime", resp.get("createTime", ""))
        # Format timestamp to match Google Forms style: M/D/YYYY H:MM:SS
        timestamp = _format_timestamp(timestamp)
        email = resp.get("respondentEmail", "")

        # Get the raw name they entered as fallback
        raw_name = ""
        if name_qid:
            name_ans = resp.get("answers", {}).get(name_qid)
            if name_ans and "textAnswers" in name_ans:
                raw_name = name_ans["textAnswers"]["answers"][0].get("value", "")

        answers = resp.get("answers", {})
        row = [timestamp, email]
        for q_id, title in questions:
            answer_data = answers.get(q_id)
            if answer_data and "textAnswers" in answer_data:
                values = [
                    a.get("value", "")
                    for a in answer_data["textAnswers"]["answers"]
                ]
                value = ", ".join(values)
                # Replace the Name field with canonical name
                if q_id == name_qid:
                    value = canonical_name(email, value)
                row.append(value)
            else:
                # If this is the name field and empty, still use canonical name
                if q_id == name_qid:
                    row.append(canonical_name(email, raw_name))
                else:
                    row.append("")
        rows.append(row)

    # Sort by timestamp (earliest first)
    rows.sort(key=lambda r: r[0])

    return headers, rows


def _format_timestamp(iso_ts: str) -> str:
    """Convert ISO 8601 timestamp to Google Forms style: M/D/YYYY H:MM:SS."""
    if not iso_ts:
        return ""
    try:
        from datetime import datetime, timezone

        dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        # Convert to US Eastern for consistency with typical form usage
        from zoneinfo import ZoneInfo

        dt = dt.astimezone(ZoneInfo("America/New_York"))
        return dt.strftime("%-m/%-d/%Y %-H:%M:%S")
    except Exception:
        return iso_ts
