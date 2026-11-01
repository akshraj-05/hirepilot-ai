"""Create Google Calendar events with optional Google Meet links."""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Any

from googleapiclient.discovery import build

from app.services.google_auth import get_credentials


async def create_event(
    summary: str,
    description: str,
    start_time: datetime,
    duration_mins: int = 30,
    attendee_emails: list[str] | None = None,
    timezone: str = "Asia/Kolkata",
) -> dict[str, Any] | None:
    creds = get_credentials()
    if not creds:
        return None

    end_time = start_time + timedelta(minutes=duration_mins)

    event_body: dict[str, Any] = {
        "summary": summary,
        "description": description,
        "start": {
            "dateTime": start_time.isoformat(),
            "timeZone": timezone,
        },
        "end": {
            "dateTime": end_time.isoformat(),
            "timeZone": timezone,
        },
        "conferenceData": {
            "createRequest": {
                "requestId": f"hirepilot-{uuid.uuid4().hex[:12]}",
            }
        },
    }
    if attendee_emails:
        event_body["attendees"] = [{"email": e} for e in attendee_emails]

    def _insert() -> dict[str, Any]:
        service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        return (
            service.events()
            .insert(
                calendarId="primary",
                body=event_body,
                conferenceDataVersion=1,
                sendUpdates="all",
            )
            .execute()
        )

    return await asyncio.to_thread(_insert)
