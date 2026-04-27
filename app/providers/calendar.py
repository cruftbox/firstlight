from pathlib import Path
from datetime import datetime, timezone, timedelta
import logging

TOKEN_PATH = Path("/app/config/google_token.json")
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def get_events(calendar_ids: list) -> list:
    """Returns list of {"time", "title", "all_day"} for today. Returns [] on any failure."""
    creds = _get_credentials()
    if not creds:
        return []

    try:
        from googleapiclient.discovery import build
        service = build("calendar", "v3", credentials=creds)
    except Exception as e:
        logging.error("Calendar API build failed: %s", e)
        return []

    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    events = []

    for cal_id in calendar_ids:
        try:
            result = (
                service.events()
                .list(
                    calendarId=cal_id,
                    timeMin=today.isoformat(),
                    timeMax=tomorrow.isoformat(),
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
        except Exception as e:
            logging.error("Calendar fetch for %s failed: %s", cal_id, e)
            continue

        for item in result.get("items", []):
            start = item.get("start", {})
            if "dateTime" in start:
                dt = datetime.fromisoformat(start["dateTime"])
                time_str = dt.strftime("%I:%M %p").lstrip("0") or "12:00 AM"
                all_day = False
            else:
                time_str = "All day"
                all_day = True
            events.append({
                "time": time_str,
                "title": item.get("summary", ""),
                "all_day": all_day,
            })

    return events


def _get_credentials():
    if not TOKEN_PATH.exists():
        return None
    try:
        from google.oauth2.credentials import Credentials
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    except Exception:
        return None

    if creds.expired and creds.refresh_token:
        try:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
        except Exception:
            return None

    return creds if creds.valid else None
