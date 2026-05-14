"""Consultation domain model."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from laso.constants.sql import ConsultationSQL
from laso.enums import ConsultationType, ConsultationStatus
from laso.utils.db import execute, execute_one, insert

log = logging.getLogger(__name__)


@dataclass
class Consultation:
    consultation_id: str
    patient_id: str
    doctor_id: str
    programme_id: str
    programme_step_id: Optional[str] = None
    type: ConsultationType = ConsultationType.INITIAL
    duration_minutes: int = 0
    status: ConsultationStatus = ConsultationStatus.NEEDS_SCHEDULING
    scheduled_at: Optional[datetime] = None
    meet_link: Optional[str] = None
    cancel_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "consultation_id": self.consultation_id,
            "patient_id": self.patient_id,
            "doctor_id": self.doctor_id,
            "programme_id": self.programme_id,
            "programme_step_id": self.programme_step_id,
            "type": self.type.value,
            "duration_minutes": self.duration_minutes,
            "status": self.status.value,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "meet_link": self.meet_link,
            "cancel_reason": self.cancel_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_row(cls, row: Dict) -> "Consultation":
        return cls(
            consultation_id=row["consultation_id"],
            patient_id=row["patient_id"],
            doctor_id=row["doctor_id"],
            programme_id=row["programme_id"],
            programme_step_id=row.get("programme_step_id"),
            type=ConsultationType(row["type"]),
            duration_minutes=row.get("duration_minutes", 0),
            status=ConsultationStatus(row["status"]),
            scheduled_at=row.get("scheduled_at"),
            meet_link=row.get("meet_link"),
            cancel_reason=row.get("cancel_reason"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def save(self) -> None:
        log.info("Consultation.save | consultation_id=%s", self.consultation_id)
        insert(
            ConsultationSQL.INSERT,
            (self.consultation_id, self.patient_id, self.doctor_id, self.programme_id,
             self.programme_step_id, self.type.value, self.duration_minutes,
             self.status.value, self.scheduled_at, self.meet_link, self.cancel_reason),
        )
        log.info("Consultation.save | success | consultation_id=%s", self.consultation_id)

    @classmethod
    def get_by_id(cls, consultation_id: str) -> Optional["Consultation"]:
        row = execute_one(ConsultationSQL.GET_BY_ID, (consultation_id,))
        return cls.from_row(row) if row else None

    @classmethod
    def list_for_patient(cls, patient_id: str) -> List["Consultation"]:
        rows = execute(ConsultationSQL.LIST_FOR_PATIENT, (patient_id,))
        return [cls.from_row(r) for r in rows]

    @classmethod
    def list_for_doctor(cls, doctor_id: str) -> List["Consultation"]:
        rows = execute(ConsultationSQL.LIST_FOR_DOCTOR, (doctor_id,))
        return [cls.from_row(r) for r in rows]

    @classmethod
    def get_for_date(cls, doctor_id: str, target_date) -> List["Consultation"]:
        rows = execute(ConsultationSQL.GET_FOR_DATE, (doctor_id, target_date))
        return [cls.from_row(r) for r in rows]

    @classmethod
    def get_upcoming(cls, doctor_id: str) -> List["Consultation"]:
        rows = execute(ConsultationSQL.GET_UPCOMING_FOR_DOCTOR, (doctor_id, datetime.utcnow()))
        return [cls.from_row(r) for r in rows]

    @classmethod
    def get_upcoming_for_patient(cls, patient_id: str) -> List["Consultation"]:
        rows = execute(ConsultationSQL.GET_UPCOMING_FOR_PATIENT, (patient_id, datetime.utcnow()))
        return [cls.from_row(r) for r in rows]
