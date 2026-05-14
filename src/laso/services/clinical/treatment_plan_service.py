"""Treatment plan service."""

import logging
from uuid import uuid4

from laso.exceptions import NotFoundError
from laso.models.treatment_plan import TreatmentPlan

log = logging.getLogger(__name__)


def get_or_create(programme_id: str, patient_id: str, doctor_id: str) -> dict:
    """Return existing plan or create a blank one."""
    log.info("treatment_plan_service.get_or_create | programme_id=%s", programme_id)
    plan = TreatmentPlan.get_for_programme(programme_id)
    if plan:
        return plan.to_dict()
    plan = TreatmentPlan(
        plan_id=str(uuid4()),
        patient_id=patient_id,
        programme_id=programme_id,
        doctor_id=doctor_id,
    )
    plan.save()
    return plan.to_dict()


def update(programme_id: str, body: dict) -> dict:
    """Update treatment plan fields."""
    log.info("treatment_plan_service.update | programme_id=%s", programme_id)
    plan = TreatmentPlan.get_for_programme(programme_id)
    if not plan:
        raise NotFoundError("Treatment plan not found for this programme")
    allowed = {
        "diagnosis_notes", "target_dose", "target_dose_unit", "titration_schedule",
        "diet_guidelines", "activity_target", "weight_target_kg", "glucose_target",
    }
    fields = {k: v for k, v in body.items() if k in allowed}
    updated = TreatmentPlan.update(programme_id, fields)
    return updated.to_dict()
