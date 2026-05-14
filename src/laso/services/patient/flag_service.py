"""Flag service — create, clear, and list patient flags."""

import logging
from uuid import uuid4

from laso.enums import FlagType
from laso.exceptions import NotFoundError
from laso.models.patient_flag import PatientFlag

log = logging.getLogger(__name__)


def set_flag(patient_id: str, flag_type: str, reason: str, created_by: str) -> dict | None:
    """Create a flag if no active flag of the same type exists. Returns flag dict or None."""
    log.info("flag_service.set_flag | patient_id=%s flag_type=%s", patient_id, flag_type)

    active = PatientFlag.get_active_flags(patient_id)
    if any(f.flag_type.value == flag_type for f in active):
        log.info("flag_service.set_flag | already active, skipping")
        return None

    flag = PatientFlag(
        flag_id=str(uuid4()),
        patient_id=patient_id,
        flag_type=FlagType(flag_type),
        reason=reason,
        created_by=created_by,
    )
    flag.save()

    log.info("flag_service.set_flag | created flag_id=%s", flag.flag_id)
    return flag.to_dict()


def clear_flag(flag_id: str, cleared_by: str) -> dict:
    """Clear a flag by setting cleared_at and cleared_by."""
    log.info("flag_service.clear_flag | flag_id=%s cleared_by=%s", flag_id, cleared_by)

    flag = PatientFlag.clear(flag_id, cleared_by)
    if not flag:
        raise NotFoundError("Flag not found")

    log.info("flag_service.clear_flag | done flag_id=%s", flag_id)
    return flag.to_dict()


def get_active_flags(patient_id: str) -> list:
    """Return all active (uncleared) flags for a patient."""
    log.info("flag_service.get_active_flags | patient_id=%s", patient_id)
    return [f.to_dict() for f in PatientFlag.get_active_flags(patient_id)]
