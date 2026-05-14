"""Consultation service — scheduling, status transitions, queries."""

import logging
from datetime import date, datetime

from laso.constants.sql import ConsultationSQL
from laso.enums.consultation import ConsultationStatus
from laso.exceptions import NotFoundError
from laso.models.consultation import Consultation
from laso.services.scheduling_validator import validate_doctor_availability
from laso.services.task_service import create_task
from laso.constants.messages import TASK_TITLES
from laso.enums.task import TaskPriority
from laso.utils.validation import validate_transition

log = logging.getLogger(__name__)


def schedule(consultation_id: str, doctor_id: str, scheduled_at: str) -> dict:
    """Validate availability and schedule the consultation."""
    log.info("consultation_service.schedule | consultation_id=%s doctor_id=%s", consultation_id, doctor_id)

    consult = Consultation.get_by_id(consultation_id)
    if not consult:
        raise NotFoundError("Consultation not found")

    scheduled_dt = datetime.fromisoformat(scheduled_at)
    validate_doctor_availability(doctor_id, scheduled_dt, duration_min=30)

    validate_transition(consult.status, ConsultationStatus.SCHEDULED, ConsultationStatus)
    from laso.utils.db import execute as db_exec
    db_exec(ConsultationSQL.UPDATE_SCHEDULE, (doctor_id, scheduled_dt, consultation_id))
    consult.status = ConsultationStatus.SCHEDULED
    log.info("consultation_service.schedule | done consultation_id=%s", consultation_id)
    return consult.to_dict()


def add_meet_link(consultation_id: str, link: str) -> dict:
    """Attach a video meeting link to the consultation."""
    log.info("consultation_service.add_meet_link | consultation_id=%s", consultation_id)
    consult = Consultation.get_by_id(consultation_id)
    if not consult:
        raise NotFoundError("Consultation not found")
    from laso.utils.db import execute as db_exec
    db_exec(ConsultationSQL.UPDATE_MEET_LINK, (link, consultation_id))
    consult.meet_link = link
    log.info("consultation_service.add_meet_link | done")
    return consult.to_dict()


def update_status(consultation_id: str, status: str, reason: str = None) -> dict:
    """Validate transition and apply side effects."""
    log.info("consultation_service.update_status | consultation_id=%s status=%s", consultation_id, status)

    consult = Consultation.get_by_id(consultation_id)
    if not consult:
        raise NotFoundError("Consultation not found")

    target = ConsultationStatus(status)
    validate_transition(consult.status, target, ConsultationStatus)
    from laso.utils.db import execute as db_exec
    db_exec(ConsultationSQL.UPDATE_STATUS, (target.value, reason, consultation_id))
    consult.status = target

    if target == ConsultationStatus.COMPLETED and consult.programme_step_id and consult.programme_id:
        from laso.services.programme_service import complete_step
        complete_step(consult.programme_id, consult.programme_step_id)

    elif target == ConsultationStatus.NO_SHOW:
        create_task(
            patient_id=consult.patient_id,
            task_type="reschedule_no_show",
            title=TASK_TITLES["reschedule_no_show"],
            priority=TaskPriority.HIGH,
        )

    log.info("consultation_service.update_status | done consultation_id=%s", consultation_id)
    return consult.to_dict()


def get_by_id(consultation_id: str) -> dict:
    """Get consultation by ID or raise NotFoundError."""
    log.info("consultation_service.get_by_id | consultation_id=%s", consultation_id)
    consult = Consultation.get_by_id(consultation_id)
    if not consult:
        raise NotFoundError("Consultation not found")
    return consult.to_dict()


def list_for_patient(patient_id: str) -> list:
    """List all consultations for a patient."""
    log.info("consultation_service.list_for_patient | patient_id=%s", patient_id)
    return [c.to_dict() for c in Consultation.list_for_patient(patient_id)]


def list_for_doctor(doctor_id: str) -> list:
    """List all consultations for a doctor."""
    log.info("consultation_service.list_for_doctor | doctor_id=%s", doctor_id)
    return [c.to_dict() for c in Consultation.list_for_doctor(doctor_id)]


def get_today(doctor_id: str) -> list:
    """Get today's consultations for a doctor."""
    log.info("consultation_service.get_today | doctor_id=%s", doctor_id)
    return [c.to_dict() for c in Consultation.get_for_date(doctor_id, date.today())]


def get_upcoming(doctor_id: str) -> list:
    log.info("consultation_service.get_upcoming | doctor_id=%s", doctor_id)
    return [c.to_dict() for c in Consultation.get_upcoming(doctor_id)]


def get_upcoming_for_patient(patient_id: str) -> list:
    log.info("consultation_service.get_upcoming_for_patient | patient_id=%s", patient_id)
    return [c.to_dict() for c in Consultation.get_upcoming_for_patient(patient_id)]
