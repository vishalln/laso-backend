"""Step activation logic — next-step resolution and side-effect creation."""

import logging
from typing import Optional
from uuid import uuid4

from laso.enums.programme import AutoActivateRule, StepStatus, StepType
from laso.enums.blood_test import BloodTestStatus
from laso.enums.consultation import ConsultationStatus
from laso.models.programme import ProgrammeStep
from laso.models.blood_test import BloodTest
from laso.models.consultation import Consultation
from laso.services.task_service import create_task
from laso.constants.messages import TASK_TITLES
from laso.enums.task import TaskPriority

log = logging.getLogger(__name__)


def activate_next_step(programme_id: str, completed_sort_order: int) -> Optional[str]:
    """Find and activate the next pending step after the completed one."""
    log.info("step_activation.activate_next_step | programme_id=%s after_order=%d", programme_id, completed_sort_order)
    steps = ProgrammeStep.list_for_programme(programme_id)
    pending = [s for s in steps if s.sort_order > completed_sort_order and s.status == StepStatus.PENDING]

    if not pending:
        log.info("step_activation.activate_next_step | no pending steps")
        return None

    next_step = pending[0]

    if next_step.auto_activate_rule == AutoActivateRule.MANUAL:
        log.info("step_activation.activate_next_step | manual step skipped step_id=%s", next_step.step_id)
        return None

    from laso.utils.db import execute as db_exec
    db_exec("UPDATE programme_steps SET status='active', activated_at=NOW() WHERE step_id=%s", (next_step.step_id,))
    next_step.status = StepStatus.ACTIVE

    patient_id = _get_patient_id(programme_id)
    on_step_activated(next_step.to_dict(), programme_id, patient_id)

    log.info("step_activation.activate_next_step | activated step_id=%s", next_step.step_id)
    return next_step.step_id


def on_step_activated(step: dict, programme_id: str, patient_id: str):
    """Create related records when a step becomes active."""
    step_type = step.get("step_type")
    step_id = step.get("step_id")
    log.info("step_activation.on_step_activated | step_id=%s type=%s", step_id, step_type)

    if step_type == StepType.BLOOD_TEST:
        blood_test = BloodTest(
            blood_test_id=str(uuid4()),
            programme_id=programme_id,
            patient_id=patient_id,
            programme_step_id=step_id,
            status=BloodTestStatus.ORDERED,
        )
        blood_test.save()
        create_task(
            patient_id=patient_id,
            task_type="enter_blood_results",
            title=TASK_TITLES["enter_blood_results"],
            priority=TaskPriority.HIGH,
        )

    elif step_type == StepType.CONSULTATION:
        consultation = Consultation(
            consultation_id=str(uuid4()),
            programme_id=programme_id,
            patient_id=patient_id,
            programme_step_id=step_id,
            doctor_id=None,
            status=ConsultationStatus.NEEDS_SCHEDULING,
        )
        consultation.save()
        create_task(
            patient_id=patient_id,
            task_type="schedule_consultation",
            title=TASK_TITLES["schedule_consultation"],
            priority=TaskPriority.HIGH,
        )

    # check_in type — no special record needed


def _get_patient_id(programme_id: str) -> str:
    """Helper to fetch patient_id from programme."""
    from laso.models.programme import Programme
    programme = Programme.get_by_id(programme_id)
    return programme.patient_id if programme else ""
