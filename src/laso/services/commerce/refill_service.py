"""Refill service — request medication refill."""

import logging
from datetime import date, timedelta

from laso.exceptions import ValidationError
from laso.models.prescription import Prescription
from laso.services.task_service import create_task
from laso.constants.messages import TASK_TITLES
from laso.models.patient import Patient

log = logging.getLogger(__name__)


def request_refill(patient_id: str, programme_id: str) -> dict:
    """Validate active prescription and create a refill task."""
    log.info("refill_service.request_refill | patient_id=%s programme_id=%s", patient_id, programme_id)

    prescription = Prescription.get_active(patient_id)
    if not prescription:
        raise ValidationError("No active prescription found")

    patient = Patient.get_by_id(patient_id)
    patient_name = patient.name if patient else "Patient"

    title = TASK_TITLES["refill_request"].format(patient_name=patient_name)
    due_date = (date.today() + timedelta(days=1)).isoformat()

    task_id = create_task(
        patient_id=patient_id,
        task_type="refill_request",
        title=title,
        priority="medium",
        due_date=due_date,
    )

    log.info("refill_service.request_refill | task_id=%s", task_id)
    return {"task_id": task_id, "message": "Refill request submitted successfully"}
