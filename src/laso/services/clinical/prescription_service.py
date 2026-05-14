"""Prescription service — create, cancel, query prescriptions."""

import logging
from uuid import uuid4

from laso.enums.prescription import PrescriptionStatus
from laso.enums.programme import StepStatus, StepType
from laso.exceptions import NotFoundError
from laso.models.prescription import Prescription
from laso.models.programme import ProgrammeStep
from laso.services.task_service import create_task
from laso.constants.messages import TASK_TITLES
from laso.enums.task import TaskPriority
from laso.utils.validation import validate_transition

log = logging.getLogger(__name__)


def create(body: dict, doctor_id: str) -> dict:
    log.info("prescription_service.create | patient_id=%s doctor_id=%s", body.get("patient_id"), doctor_id)
    from laso.utils.db import update_by_id
    from laso.utils.validation import validate_required

    validate_required(body, ["patient_id", "medication"])
    patient_id = body["patient_id"]

    current = Prescription.get_active(patient_id)
    if current:
        update_by_id("prescriptions", "prescription_id", current.prescription_id,
                     status=PrescriptionStatus.SUPERSEDED.value)

    # Create new prescription
    rx = Prescription(
        prescription_id=str(uuid4()),
        patient_id=patient_id,
        doctor_id=doctor_id,
        programme_id=body.get("programme_id", ""),
        medication=body["medication"],
        dose_value=body.get("dose_value"),
        dose_unit=body.get("dose_unit"),
        frequency=body.get("frequency"),
        duration_weeks=body.get("duration_weeks"),
        status=PrescriptionStatus.ACTIVE,
    )
    rx.save()

    # Complete active prescription/dose_review step if present
    if body.get("programme_id"):
        steps = ProgrammeStep.list_for_programme(body["programme_id"])
        active_rx_step = next(
            (s for s in steps if s.status == StepStatus.ACTIVE and s.step_type in (StepType.PRESCRIPTION,)),
            None,
        )
        if active_rx_step:
            from laso.services.programme_service import complete_step
            complete_step(body["programme_id"], active_rx_step.step_id)

    # Create order task
    create_task(
        patient_id=patient_id,
        task_type="create_order",
        title=TASK_TITLES["create_order"],
        priority=TaskPriority.MEDIUM,
    )

    log.info("prescription_service.create | prescription_id=%s", rx.prescription_id)
    return rx.to_dict()


def cancel(prescription_id: str, reason: str) -> dict:
    """Cancel an active prescription."""
    log.info("prescription_service.cancel | prescription_id=%s", prescription_id)

    rx = Prescription.get_by_id(prescription_id)
    if not rx:
        raise NotFoundError("Prescription not found")

    validate_transition(rx.status, PrescriptionStatus.CANCELLED, PrescriptionStatus)
    rx.status = PrescriptionStatus.CANCELLED
    rx.cancel_reason = reason
    rx.save()

    log.info("prescription_service.cancel | done prescription_id=%s", prescription_id)
    return rx.to_dict()


def get_active(patient_id: str) -> dict:
    """Get active prescription for patient or raise NotFoundError."""
    log.info("prescription_service.get_active | patient_id=%s", patient_id)
    rx = Prescription.get_active(patient_id)
    if not rx:
        raise NotFoundError("No active prescription found")
    return rx.to_dict()


def list_for_patient(patient_id: str) -> list:
    """List all prescriptions for a patient."""
    log.info("prescription_service.list_for_patient | patient_id=%s", patient_id)
    return [rx.to_dict() for rx in Prescription.list_for_patient(patient_id)]
