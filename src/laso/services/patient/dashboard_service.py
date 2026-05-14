"""Dashboard service — compute next action for a patient."""

import logging
from datetime import datetime, timedelta

from laso.models.check_in import WeeklyCheckIn
from laso.models.programme import Programme
from laso.utils.db import execute_one

log = logging.getLogger(__name__)


def compute_next_action(patient_id: str, programme_id: str) -> dict:
    """Priority logic for the patient's next action card."""
    log.info("dashboard_service.compute_next_action | patient_id=%s", patient_id)

    programme = Programme.get_by_id(programme_id)
    now = datetime.utcnow()

    # 1) Check-in needed this week
    latest = WeeklyCheckIn.get_latest(patient_id)
    if not latest or (now - latest.submitted_at).days >= 7:
        return {
            "action_type": "check_in",
            "title": "Weekly check-in due",
            "description": "Submit your weekly check-in to track progress",
            "link": f"/programmes/{programme_id}/check-in",
            "metadata": {},
        }

    # 2) Consultation within 15 minutes
    consultation = execute_one(
        """SELECT * FROM consultations WHERE patient_id = %s
           AND scheduled_at BETWEEN %s AND %s AND status = 'scheduled' LIMIT 1""",
        (patient_id, now, now + timedelta(minutes=15)),
    )
    if consultation:
        return {
            "action_type": "consultation",
            "title": "Consultation starting soon",
            "description": "Your consultation begins within 15 minutes",
            "link": f"/consultations/{consultation['consultation_id']}",
            "metadata": {"consultation_id": consultation["consultation_id"]},
        }

    # 3) Blood results in last 24 hours
    blood_result = execute_one(
        """SELECT * FROM blood_tests WHERE patient_id = %s
           AND status = 'results_ready' AND updated_at >= %s LIMIT 1""",
        (patient_id, now - timedelta(hours=24)),
    )
    if blood_result:
        return {
            "action_type": "blood_results",
            "title": "New blood test results",
            "description": "Your blood test results are ready to review",
            "link": f"/blood-tests/{blood_result['blood_test_id']}",
            "metadata": {"blood_test_id": blood_result["blood_test_id"]},
        }

    # 4) New prescription in last 24 hours
    prescription = execute_one(
        """SELECT * FROM prescriptions WHERE patient_id = %s
           AND status = 'active' AND created_at >= %s LIMIT 1""",
        (patient_id, now - timedelta(hours=24)),
    )
    if prescription:
        return {
            "action_type": "prescription",
            "title": "New prescription available",
            "description": "A new prescription has been created for you",
            "link": f"/prescriptions/{prescription['prescription_id']}",
            "metadata": {"prescription_id": prescription["prescription_id"]},
        }

    # 5) No action needed
    return {
        "action_type": "none",
        "title": "All caught up",
        "description": "No pending actions at this time",
        "link": None,
        "metadata": {},
    }
