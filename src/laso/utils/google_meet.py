"""Google Meet session management via Google Calendar API with a Service Account."""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

from google.oauth2 import service_account
from googleapiclient.discovery import build

from laso.constants.google_calendar import GCAL_DEFAULTS, GCAL_ERRORS, GCAL_SCOPE, GOOGLE_CALENDAR

log = logging.getLogger(__name__)

_SCOPES = [GCAL_SCOPE.CALENDAR]


def _build_service(credentials_path: Optional[str], credentials_dict: Optional[Dict]):
    """Build an authenticated Google Calendar API service from file path or dict."""
    log.info("_build_service | loading credentials", extra={
        "source": "file" if credentials_path else "dict"
    })
    creds = (
        service_account.Credentials.from_service_account_file(credentials_path, scopes=_SCOPES)
        if credentials_path
        else service_account.Credentials.from_service_account_info(credentials_dict, scopes=_SCOPES)
    )
    service = build("calendar", "v3", credentials=creds, num_retries=GOOGLE_CALENDAR.max_retries)
    log.info("_build_service | service ready", extra={"service_account": creds.service_account_email})
    return service


def _to_aware(dt: datetime, tz: str) -> datetime:
    """Ensure datetime is timezone-aware; assume `tz` if naive."""
    return dt if dt.tzinfo else dt.replace(tzinfo=ZoneInfo(tz))


def _extract_meet_link(event: Dict) -> Optional[str]:
    """Pull the Google Meet URI from a Calendar event response."""
    for ep in event.get("conferenceData", {}).get("entryPoints", []):
        if ep.get("entryPointType") == "video":
            return ep["uri"]
    return None


class GoogleMeetClient:
    """Creates and manages Google Meet sessions backed by Google Calendar events.

    Accepts credentials either from a local file path (dev) or a pre-loaded dict
    (Lambda / Secrets Manager). Exactly one must be provided.
    """

    def __init__(
        self,
        calendar_id: str = GCAL_DEFAULTS.CALENDAR_ID,
        credentials_path: Optional[str] = None,
        credentials_dict: Optional[Dict] = None,
    ) -> None:
        if not (credentials_path or credentials_dict):
            raise ValueError(GCAL_ERRORS.CREDENTIAL_REQUIRED)
        self.calendar_id = calendar_id
        self._svc = _build_service(credentials_path, credentials_dict)
        log.info("GoogleMeetClient ready", extra={"calendar_id": calendar_id})

    # ── Public API ────────────────────────────────────────────────────────────

    def create_meet_session(
        self,
        title: str,
        start_time: datetime,
        duration_minutes: int = GOOGLE_CALENDAR.default_duration_minutes,
        attendee_emails: Optional[List[str]] = None,
        description: str = GCAL_DEFAULTS.DESCRIPTION,
    ) -> Dict:
        """Create a Calendar event with a Google Meet link and return session details."""
        start = _to_aware(start_time, GCAL_DEFAULTS.TIMEZONE)
        end = start + timedelta(minutes=duration_minutes)

        body = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start.isoformat(), "timeZone": GCAL_DEFAULTS.TIMEZONE},
            "end":   {"dateTime": end.isoformat(),   "timeZone": GCAL_DEFAULTS.TIMEZONE},
            "conferenceData": {"createRequest": {"requestId": str(uuid.uuid4()), "conferenceSolutionKey": {"type": "hangoutsMeet"}}},
            **({"attendees": [{"email": e} for e in attendee_emails]} if attendee_emails else {}),
        }

        log.info("create_meet_session | request", extra={
            "title": title, "start": start.isoformat(), "duration_minutes": duration_minutes,
            "attendees": attendee_emails,
        })

        event = (
            self._svc.events()
            .insert(calendarId=self.calendar_id, body=body, conferenceDataVersion=1, sendUpdates="all")
            .execute()
        )

        meet_link = _extract_meet_link(event)
        log.info("create_meet_session | success", extra={
            "event_id": event["id"], "meet_link": meet_link,
            "start": start.isoformat(), "end": end.isoformat(),
        })

        return {
            "event_id":          event["id"],
            "meet_link":         meet_link,
            "start_time":        start.isoformat(),
            "end_time":          end.isoformat(),
            "calendar_event_url": event.get("htmlLink"),
        }

    def get_event(self, event_id: str) -> Dict:
        """Fetch a Calendar event by ID."""
        log.info("get_event | request", extra={"event_id": event_id})
        event = self._svc.events().get(calendarId=self.calendar_id, eventId=event_id).execute()
        log.info("get_event | success", extra={"event_id": event_id, "status": event.get("status")})
        return event

    def cancel_event(self, event_id: str) -> None:
        """Cancel (delete) a Calendar event."""
        log.info("cancel_event | request", extra={"event_id": event_id})
        self._svc.events().delete(calendarId=self.calendar_id, eventId=event_id, sendUpdates="all").execute()
        log.info("cancel_event | success", extra={"event_id": event_id})
