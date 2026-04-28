from pathlib import Path
from datetime import datetime, timezone, timedelta
import logging
import pytz

TOKEN_PATH = Path("/app/config/google_token.json")
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def get_events(calendar_ids: list, day_offset: int = 0, timezone_str: str = "America/Los_Angeles") -> list:
    """Return list of {"time", "title", "all_day"} for today + day_offset. Returns [] on any failure."""
    creds = _get_credentials()
    if not creds:
        return []

    try:
        from googleapiclient.discovery import build
        service = build("calendar", "v3", credentials=creds)
    except Exception as e:
        logging.error("Calendar API build failed: %s", e)
        return []

    try:
        tz = pytz.timezone(timezone_str)
    except Exception:
        tz = pytz.utc
    now_local = datetime.now(tz)
    day_start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=day_offset)
    day_start = day_start_local.astimezone(timezone.utc)
    day_end = (day_start_local + timedelta(days=1)).astimezone(timezone.utc)
    events = []

    for cal_id in calendar_ids:
        try:
            result = (
                service.events()
                .list(
                    calendarId=cal_id,
                    timeMin=day_start.isoformat(),
                    timeMax=day_end.isoformat(),
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
                sort_key = dt.astimezone(timezone.utc)
            else:
                date_str = start.get("date", "")
                time_str = "All day"
                all_day = True
                sort_key = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc) if date_str else day_start
            events.append({
                "time": time_str,
                "title": item.get("summary", ""),
                "all_day": all_day,
                "_sort": sort_key,
            })

    events.sort(key=lambda e: e["_sort"])
    for e in events:
        del e["_sort"]
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
