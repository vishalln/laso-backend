"""Programme lifecycle service — creation, status transitions, step management."""

import logging
from uuid import uuid4

from laso.enums.programme import ProgrammeStatus, StepStatus, StepType
from laso.exceptions import ConflictError, NotFoundError
from laso.models.programme import Programme, ProgrammeStep
from laso.utils.validation import validate_transition

from laso.services.step_activation import activate_next_step, on_step_activated
from laso.services.payment_service import initiate as initiate_payment
from laso.services.task_service import create_task
from laso.constants.messages import TASK_TITLES
from laso.constants.programme import PAYMENT_AMOUNT_INR

log = logging.getLogger(__name__)


def create(patient_id: str, template_id: str) -> dict:
    """Create a new programme from template. Raises ConflictError if one is active."""
    log.info("programme_service.create | patient_id=%s template_id=%s", patient_id, template_id)

    existing = Programme.get_active(patient_id)
    if existing:
        raise ConflictError("Patient already has an active programme")

    programme_id = str(uuid4())

    # Get template info for name/version
    from laso.models.protocol import ProtocolTemplate
    template = ProtocolTemplate.get_by_id(template_id)
    template_name = template.name if template else "Programme"
    template_version = template.version if template else 1

    from datetime import date as date_type
    # Create programme first (payment has FK to programme)
    programme = Programme(
        programme_id=programme_id,
        patient_id=patient_id,
        doctor_id=None,
        template_id=template_id,
        template_version=template_version,
        name=template_name,
        status=ProgrammeStatus.ACTIVE,
        start_date=date_type.today(),
    )
    programme.save()

    # Payment stub (after programme exists for FK)
    initiate_payment(programme_id, patient_id, PAYMENT_AMOUNT_INR)

    # Stamp template steps
    steps = ProgrammeStep.create_from_template(programme_id, template_id)

    # Activate first step if rule is on_programme_start
    from laso.enums.programme import AutoActivateRule as AAR
    from laso.utils.db import execute as db_execute
    if steps:
        first_step = steps[0]
        if first_step.auto_activate_rule == AAR.ON_PROGRAMME_START:
            db_execute("UPDATE programme_steps SET status='active', activated_at=NOW() WHERE step_id=%s",
                       (first_step.step_id,))
            first_step.status = StepStatus.ACTIVE
            on_step_activated(first_step.to_dict(), programme_id, patient_id)

    log.info("programme_service.create | programme_id=%s steps=%d", programme_id, len(steps))
    return programme.to_dict()


def get_active(patient_id: str) -> dict:
    """Return active programme or raise NotFoundError."""
    log.info("programme_service.get_active | patient_id=%s", patient_id)
    programme = Programme.get_active(patient_id)
    if not programme:
        raise NotFoundError("No active programme found")
    return programme.to_dict()


def get_by_id(programme_id: str) -> dict:
    """Return programme by ID or raise NotFoundError."""
    log.info("programme_service.get_by_id | programme_id=%s", programme_id)
    programme = Programme.get_by_id(programme_id)
    if not programme:
        raise NotFoundError("Programme not found")
    return programme.to_dict()


def get_history(patient_id: str) -> list:
    """Return all programmes for patient."""
    log.info("programme_service.get_history | patient_id=%s", patient_id)
    return [p.to_dict() for p in Programme.list_for_patient(patient_id)]


def get_steps(programme_id: str) -> list:
    """Return all steps for a programme."""
    log.info("programme_service.get_steps | programme_id=%s", programme_id)
    return [s.to_dict() for s in ProgrammeStep.list_for_programme(programme_id)]


def update_status(programme_id: str, status: str, reason: str = None) -> dict:
    """Validate and apply programme status transition."""
    log.info("programme_service.update_status | programme_id=%s status=%s", programme_id, status)
    programme = Programme.get_by_id(programme_id)
    if not programme:
        raise NotFoundError("Programme not found")

    target = ProgrammeStatus(status)
    validate_transition(programme.status, target, ProgrammeStatus)

    steps = ProgrammeStep.list_for_programme(programme_id)

    if target == ProgrammeStatus.PAUSED:
        active_step = next((s for s in steps if s.status == StepStatus.ACTIVE), None)
        programme.paused_at_step_id = active_step.step_id if active_step else None
        if active_step:
            active_step.status = StepStatus.PENDING
            active_step.save()

    elif target == ProgrammeStatus.ACTIVE and programme.status == ProgrammeStatus.PAUSED:
        paused_step = next((s for s in steps if s.step_id == programme.paused_at_step_id), None)
        if paused_step:
            paused_step.status = StepStatus.ACTIVE
            paused_step.save()
        programme.paused_at_step_id = None

    elif target == ProgrammeStatus.COMPLETED:
        for s in steps:
            if s.status in (StepStatus.PENDING, StepStatus.ACTIVE):
                s.status = StepStatus.SKIPPED
                s.save()

    elif target == ProgrammeStatus.CANCELLED:
        for s in steps:
            if s.status != StepStatus.COMPLETED:
                s.status = StepStatus.SKIPPED
                s.save()

    programme.status = target
    programme.cancel_reason = reason
    programme.save()

    log.info("programme_service.update_status | done programme_id=%s", programme_id)
    return programme.to_dict()


def add_step(programme_id: str, body: dict) -> dict:
    """Insert a new step at a given position, reordering sort_orders."""
    log.info("programme_service.add_step | programme_id=%s", programme_id)
    steps = ProgrammeStep.list_for_programme(programme_id)
    insert_after_id = body.get("insert_after_step_id")

    insert_idx = 0
    if insert_after_id:
        insert_idx = next((i + 1 for i, s in enumerate(steps) if s.step_id == insert_after_id), len(steps))

    # Reorder subsequent steps
    for s in steps[insert_idx:]:
        s.sort_order += 1
        s.save()

    new_step = ProgrammeStep(
        step_id=str(uuid4()),
        programme_id=programme_id,
        step_type=body["step_type"],
        title=body.get("title", ""),
        sort_order=insert_idx,
        status=StepStatus.PENDING,
    )
    new_step.save()

    log.info("programme_service.add_step | step_id=%s sort_order=%d", new_step.step_id, new_step.sort_order)
    return new_step.to_dict()


def complete_step(programme_id: str, step_id: str) -> dict:
    """Mark step completed and activate next."""
    log.info("programme_service.complete_step | programme_id=%s step_id=%s", programme_id, step_id)
    from laso.utils.db import execute as db_exec

    step = ProgrammeStep.get_by_id(step_id)
    if not step:
        raise NotFoundError("Step not found")

    validate_transition(step.status, StepStatus.COMPLETED, StepStatus)
    db_exec("UPDATE programme_steps SET status='completed', completed_at=NOW() WHERE step_id=%s", (step_id,))
    step.status = StepStatus.COMPLETED

    activate_next_step(programme_id, step.sort_order)

    log.info("programme_service.complete_step | completed step_id=%s", step_id)
    return step.to_dict()


def skip_step(programme_id: str, step_id: str, reason: str) -> dict:
    """Mark step skipped and activate next."""
    log.info("programme_service.skip_step | programme_id=%s step_id=%s reason=%s", programme_id, step_id, reason)
    step = ProgrammeStep.get_by_id(step_id)
    if not step:
        raise NotFoundError("Step not found")

    validate_transition(step.status, StepStatus.SKIPPED, StepStatus)
    from laso.utils.db import execute as db_exec
    db_exec("UPDATE programme_steps SET status='skipped', skip_reason=%s WHERE step_id=%s", (reason, step_id))
    step.status = StepStatus.SKIPPED

    activate_next_step(programme_id, step.sort_order)

    log.info("programme_service.skip_step | skipped step_id=%s", step_id)
    return step.to_dict()
