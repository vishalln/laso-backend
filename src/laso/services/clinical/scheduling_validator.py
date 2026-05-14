"""Scheduling validation — doctor availability checks."""

import logging
from datetime import datetime, timedelta

from laso.exceptions import ConflictError
from laso.utils.db import execute_one

log = logging.getLogger(__name__)

WORK_START_HOUR = 9
WORK_END_HOUR = 18


def validate_doctor_availability(doctor_id: str, scheduled_at: datetime, duration_min: int):
    """Check working hours and overlapping bookings. Raises ConflictError if unavailable."""
    log.info("scheduling_validator.validate | doctor_id=%s at=%s dur=%d", doctor_id, scheduled_at, duration_min)

    if scheduled_at.hour < WORK_START_HOUR or scheduled_at.hour >= WORK_END_HOUR:
        raise ConflictError(f"Doctor unavailable: outside working hours ({WORK_START_HOUR}:00-{WORK_END_HOUR}:00)")

    end_time = scheduled_at + timedelta(minutes=duration_min)
    conflict = execute_one("""
        SELECT consultation_id, scheduled_at FROM consultations
        WHERE doctor_id = %s AND status IN ('scheduled','in_progress')
          AND scheduled_at < %s
          AND scheduled_at + (duration_minutes * INTERVAL '1 minute') > %s
    """, (doctor_id, end_time, scheduled_at))

    if conflict:
        raise ConflictError("Doctor has a conflicting booking", details={
            "conflicting_consultation_id": str(conflict["consultation_id"]),
            "conflicting_time": str(conflict["scheduled_at"]),
        })

    log.info("scheduling_validator.validate | available=True")
