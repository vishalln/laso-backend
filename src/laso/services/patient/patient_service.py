"""Patient service — profile retrieval, updates, flags."""

import logging
import uuid
from typing import Dict, List

from laso.exceptions import NotFoundError
from laso.models.patient import Patient
from laso.models.patient_flag import PatientFlag
from laso.utils.db import update_by_id

log = logging.getLogger(__name__)

_UPDATABLE_FIELDS = {
    "name", "age", "gender", "city", "height_cm", "phone",
    "address_line1", "address_line2", "address_city",
    "address_state", "address_pincode",
}


def get_by_id(patient_id: str) -> Dict:
    log.info("patient_service.get_by_id | patient_id=%s", patient_id)
    patient = Patient.get_by_id(patient_id)
    if not patient:
        raise NotFoundError("Patient not found")
    return patient.to_dict()


def list_for_doctor(doctor_id: str) -> List[Dict]:
    log.info("patient_service.list_for_doctor | doctor_id=%s", doctor_id)
    patients = Patient.list_for_doctor(doctor_id)
    log.info("patient_service.list_for_doctor | count=%d", len(patients))
    return [p.to_dict() for p in patients]


def update_profile(patient_id: str, data: Dict) -> Dict:
    log.info("patient_service.update_profile | patient_id=%s fields=%s", patient_id, list(data.keys()))
    patient = Patient.get_by_id(patient_id)
    if not patient:
        raise NotFoundError("Patient not found")

    fields = {k: v for k, v in data.items() if k in _UPDATABLE_FIELDS}
    if fields:
        update_by_id("patients", "patient_id", patient_id, **fields)

    updated = Patient.get_by_id(patient_id)
    log.info("patient_service.update_profile | success | patient_id=%s", patient_id)
    return updated.to_dict()


def get_flags(patient_id: str) -> List[Dict]:
    log.info("patient_service.get_flags | patient_id=%s", patient_id)
    flags = PatientFlag.get_active_flags(patient_id)
    log.info("patient_service.get_flags | count=%d", len(flags))
    return [f.to_dict() for f in flags]


def set_flag(patient_id: str, data: Dict, user) -> Dict:
    log.info("patient_service.set_flag | patient_id=%s flag_type=%s", patient_id, data.get("flag_type"))
    flag = PatientFlag(
        flag_id=str(uuid.uuid4()),
        patient_id=patient_id,
        flag_type=data["flag_type"],
        reason=data.get("reason", ""),
        created_by=user.id,
    )
    flag.save()
    log.info("patient_service.set_flag | success | flag_id=%s", flag.flag_id)
    return flag.to_dict()


def clear_flag(patient_id: str, flag_id: str, user) -> Dict:
    log.info("patient_service.clear_flag | patient_id=%s flag_id=%s", patient_id, flag_id)
    flag = PatientFlag.clear(flag_id=flag_id, cleared_by=user.id)
    if not flag:
        raise NotFoundError("Flag not found")
    log.info("patient_service.clear_flag | success | flag_id=%s", flag_id)
    return flag.to_dict()
