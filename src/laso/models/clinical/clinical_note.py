"""Clinical note domain model."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from laso.enums import NoteType
from laso.utils.db import execute, insert

log = logging.getLogger(__name__)


@dataclass
class ClinicalNote:
    note_id: str
    patient_id: str
    doctor_id: str
    note_type: NoteType
    subject: str
    body: str
    programme_id: Optional[str] = None
    consultation_id: Optional[str] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "note_id": self.note_id,
            "patient_id": self.patient_id,
            "doctor_id": self.doctor_id,
            "note_type": self.note_type.value,
            "subject": self.subject,
            "body": self.body,
            "programme_id": self.programme_id,
            "consultation_id": self.consultation_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_row(cls, row: Dict) -> "ClinicalNote":
        return cls(
            note_id=row["note_id"],
            patient_id=row["patient_id"],
            doctor_id=row["doctor_id"],
            note_type=NoteType(row["note_type"]),
            subject=row["subject"],
            body=row["body"],
            programme_id=row.get("programme_id"),
            consultation_id=row.get("consultation_id"),
            created_at=row.get("created_at"),
        )

    def save(self) -> None:
        log.info("ClinicalNote.save | note_id=%s", self.note_id)
        insert(
            """INSERT INTO clinical_notes (note_id, patient_id, doctor_id, note_type,
               subject, body, programme_id, consultation_id)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (self.note_id, self.patient_id, self.doctor_id, self.note_type.value,
             self.subject, self.body, self.programme_id, self.consultation_id),
        )

    @classmethod
    def list_for_patient(cls, patient_id: str) -> List["ClinicalNote"]:
        rows = execute(
            "SELECT * FROM clinical_notes WHERE patient_id = %s ORDER BY created_at DESC",
            (patient_id,),
        )
        return [cls.from_row(r) for r in rows]
