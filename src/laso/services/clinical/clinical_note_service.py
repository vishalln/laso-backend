"""Clinical note service."""

import logging
from uuid import uuid4

from laso.enums import NoteType
from laso.models.clinical_note import ClinicalNote
from laso.utils.validation import validate_required, validate_enum

log = logging.getLogger(__name__)


def create(body: dict, doctor_id: str) -> dict:
    log.info("clinical_note_service.create | doctor_id=%s patient_id=%s", doctor_id, body.get("patient_id"))

    validate_required(body, ["patient_id", "note_type", "subject", "body"])
    validate_enum(body["note_type"], NoteType, "note_type")

    note = ClinicalNote(
        note_id=str(uuid4()),
        patient_id=body["patient_id"],
        doctor_id=doctor_id,
        note_type=NoteType(body["note_type"]),
        subject=body["subject"],
        body=body["body"],
        programme_id=body.get("programme_id"),
        consultation_id=body.get("consultation_id"),
    )
    note.save()

    log.info("clinical_note_service.create | success | note_id=%s", note.note_id)
    return note.to_dict()


def list_for_patient(patient_id: str) -> list:
    log.info("clinical_note_service.list_for_patient | patient_id=%s", patient_id)
    notes = ClinicalNote.list_for_patient(patient_id)
    log.info("clinical_note_service.list_for_patient | count=%d", len(notes))
    return [n.to_dict() for n in notes]
