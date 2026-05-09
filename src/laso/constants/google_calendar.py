"""Google Calendar / Meet domain constants."""

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class GoogleCalendarEnvVar:
    CREDENTIALS_PATH: Final[str] = "GOOGLE_CREDENTIALS_PATH"
    CREDENTIALS_SECRET_ARN: Final[str] = "GOOGLE_CREDENTIALS_SECRET_ARN"
    CALENDAR_ID: Final[str] = "GOOGLE_CALENDAR_ID"


@dataclass(frozen=True)
class GoogleCalendarDefaults:
    CALENDAR_ID: Final[str] = "1b7e0245625e9d9ffb0489ad126ec9245d29c22c12a422149b7ab0bffa48aa96@group.calendar.google.com"
    TIMEZONE: Final[str] = "Asia/Kolkata"
    DESCRIPTION: Final[str] = "Laso Health consultation"


@dataclass(frozen=True)
class GoogleCalendarScope:
    CALENDAR: Final[str] = "https://www.googleapis.com/auth/calendar"


@dataclass(frozen=True)
class GoogleCalendarError:
    CREDENTIAL_REQUIRED: Final[str] = "Provide credentials_path or credentials_dict"
    EVENT_CREATE_FAILED: Final[str] = "Failed to create calendar event"
    EVENT_NOT_FOUND: Final[str] = "Calendar event not found"
    EVENT_CANCEL_FAILED: Final[str] = "Failed to cancel calendar event"


@dataclass(frozen=True)
class GoogleCalendarPerformance:
    timeout_seconds: int = 10
    max_retries: int = 3
    default_duration_minutes: int = 30


GCAL_ENV: Final[GoogleCalendarEnvVar] = GoogleCalendarEnvVar()
GCAL_DEFAULTS: Final[GoogleCalendarDefaults] = GoogleCalendarDefaults()
GCAL_SCOPE: Final[GoogleCalendarScope] = GoogleCalendarScope()
GCAL_ERRORS: Final[GoogleCalendarError] = GoogleCalendarError()
GOOGLE_CALENDAR: Final[GoogleCalendarPerformance] = GoogleCalendarPerformance()
