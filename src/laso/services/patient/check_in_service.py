"""Check-in service — submission, listing, adherence queries."""

import logging
import math
from datetime import date
from uuid import uuid4

import psycopg2.errors

from laso.exceptions import ConflictError, NotFoundError
from laso.models.check_in import WeeklyCheckIn
from laso.models.programme import Programme
from laso.models.prescription import Prescription
from laso.services.adherence_calculator import compute as compute_adherence
from laso.services.flag_evaluator import evaluate_after_checkin
from laso.utils.pagination import build_paginated_query, encode_cursor
from laso.utils.db import execute

log = logging.getLogger(__name__)

FREQUENCY_DOSES = {
    "once_weekly": 1,
    "once_daily": 7,
    "twice_daily": 14,
}


def submit(patient_id: str, programme_id: str, body: dict) -> dict:
    """Submit a weekly check-in. Raises ConflictError if duplicate this week."""
    log.info("check_in_service.submit | patient_id=%s programme_id=%s", patient_id, programme_id)

    programme = Programme.get_by_id(programme_id)
    if not programme:
        raise NotFoundError("Programme not found")

    # Compute week number from programme start_date
    start = programme.start_date or date.today()
    week_number = math.floor((date.today() - start).days / 7) + 1

    # Get doses_scheduled from active prescription frequency
    prescription = Prescription.get_active(patient_id)
    doses_scheduled = FREQUENCY_DOSES.get(prescription.frequency, 7) if prescription else 7

    check_in = WeeklyCheckIn(
        check_in_id=str(uuid4()),
        patient_id=patient_id,
        programme_id=programme_id,
        programme_step_id=body.get("programme_step_id"),
        week_number=week_number,
        weight_kg=body.get("weight_kg", 0.0),
        fasting_glucose=body.get("fasting_glucose"),
        doses_taken=body.get("doses_taken", 0),
        doses_scheduled=doses_scheduled,
        side_effects=body.get("side_effects") or [],
        appetite_level=body.get("appetite_level"),
        energy_level=body.get("energy_level"),
        notes=body.get("notes"),
    )

    try:
        check_in.save()
    except psycopg2.errors.UniqueViolation:
        raise ConflictError("Check-in already submitted for this week")

    # Compute adherence and weight change
    adherence = compute_adherence(programme_id)
    check_ins = WeeklyCheckIn.list_for_programme(programme_id)
    weight_change_kg = None
    if len(check_ins) >= 2:
        weight_change_kg = round(check_ins[-1].weight_kg - check_ins[0].weight_kg, 2)

    # Evaluate auto-flags
    evaluate_after_checkin(patient_id, programme_id, body)

    result = check_in.to_dict()
    result["adherence_pct"] = adherence["adherence_pct"]
    result["weight_change_kg"] = weight_change_kg

    log.info("check_in_service.submit | check_in_id=%s", check_in.check_in_id)
    return result


def list_for_programme(programme_id: str, cursor: str = None, limit: int = 20) -> dict:
    """Paginated list of check-ins for a programme."""
    log.info("check_in_service.list_for_programme | programme_id=%s", programme_id)

    base_query = "SELECT * FROM weekly_check_ins WHERE programme_id = %s"
    query, params = build_paginated_query(base_query, "submitted_at", cursor, limit)
    params = [programme_id] + params

    rows = execute(query, tuple(params))
    items = [WeeklyCheckIn.from_row(r).to_dict() for r in rows]

    next_cursor = None
    if items:
        next_cursor = encode_cursor({"after": items[-1]["submitted_at"]})

    return {"items": items, "next_cursor": next_cursor}


def get_latest(patient_id: str) -> dict:
    """Return the most recent check-in for a patient."""
    log.info("check_in_service.get_latest | patient_id=%s", patient_id)
    check_in = WeeklyCheckIn.get_latest(patient_id)
    if not check_in:
        raise NotFoundError("No check-ins found")
    return check_in.to_dict()


def get_adherence(programme_id: str) -> dict:
    """Return adherence stats for a programme."""
    log.info("check_in_service.get_adherence | programme_id=%s", programme_id)
    return compute_adherence(programme_id)
