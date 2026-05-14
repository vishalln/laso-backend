"""Prescription domain model."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from laso.enums import PrescriptionStatus
from laso.utils.db import execute, execute_one, insert

log = logging.getLogger(__name__)


@dataclass
class Prescription:
    prescription_id: str
    patient_id: str
    doctor_id: str
    programme_id: str
    consultation_id: Optional[str] = None
    programme_step_id: Optional[str] = None
    medication: str = ""
    dose_value: Optional[float] = None
    dose_unit: Optional[str] = None
    frequency: Optional[str] = None
    duration_weeks: Optional[int] = None
    special_instructions: Optional[str] = None
    next_escalation_dose: Optional[float] = None
    next_escalation_unit: Optional[str] = None
    status: PrescriptionStatus = PrescriptionStatus.ACTIVE
    created_at: Optional[datetime] = None
    superseded_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancel_reason: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "prescription_id": self.prescription_id,
            "patient_id": self.patient_id,
            "doctor_id": self.doctor_id,
            "programme_id": self.programme_id,
            "consultation_id": self.consultation_id,
            "programme_step_id": self.programme_step_id,
            "medication": self.medication,
            "dose_value": self.dose_value,
            "dose_unit": self.dose_unit,
            "frequency": self.frequency,
            "duration_weeks": self.duration_weeks,
            "special_instructions": self.special_instructions,
            "next_escalation_dose": self.next_escalation_dose,
            "next_escalation_unit": self.next_escalation_unit,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "superseded_at": self.superseded_at.isoformat() if self.superseded_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "cancel_reason": self.cancel_reason,
        }

    @classmethod
    def from_row(cls, row: Dict) -> "Prescription":
        return cls(
            prescription_id=row["prescription_id"],
            patient_id=row["patient_id"],
            doctor_id=row["doctor_id"],
            programme_id=row["programme_id"],
            consultation_id=row.get("consultation_id"),
            programme_step_id=row.get("programme_step_id"),
            medication=row.get("medication", ""),
            dose_value=row.get("dose_value"),
            dose_unit=row.get("dose_unit"),
            frequency=row.get("frequency"),
            duration_weeks=row.get("duration_weeks"),
            special_instructions=row.get("special_instructions"),
            next_escalation_dose=row.get("next_escalation_dose"),
            next_escalation_unit=row.get("next_escalation_unit"),
            status=PrescriptionStatus(row["status"]),
            created_at=row.get("created_at"),
            superseded_at=row.get("superseded_at"),
            cancelled_at=row.get("cancelled_at"),
            cancel_reason=row.get("cancel_reason"),
        )

    def save(self) -> None:
        log.info("Prescription.save | prescription_id=%s", self.prescription_id)
        insert(
            """INSERT INTO prescriptions (prescription_id, patient_id, doctor_id, programme_id,
               consultation_id, programme_step_id, medication, dose_value, dose_unit, frequency,
               duration_weeks, special_instructions, next_escalation_dose, next_escalation_unit, status)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (self.prescription_id, self.patient_id, self.doctor_id, self.programme_id,
             self.consultation_id, self.programme_step_id, self.medication, self.dose_value,
             self.dose_unit, self.frequency, self.duration_weeks, self.special_instructions,
             self.next_escalation_dose, self.next_escalation_unit, self.status.value),
        )
        log.info("Prescription.save | success | prescription_id=%s", self.prescription_id)

    @classmethod
    def get_by_id(cls, prescription_id: str) -> Optional["Prescription"]:
        row = execute_one("SELECT * FROM prescriptions WHERE prescription_id = %s", (prescription_id,))
        return cls.from_row(row) if row else None

    @classmethod
    def get_active(cls, patient_id: str) -> Optional["Prescription"]:
        row = execute_one(
            "SELECT * FROM prescriptions WHERE patient_id = %s AND status = 'active' ORDER BY created_at DESC LIMIT 1",
            (patient_id,),
        )
        return cls.from_row(row) if row else None

    @classmethod
    def list_for_patient(cls, patient_id: str) -> List["Prescription"]:
        rows = execute(
            "SELECT * FROM prescriptions WHERE patient_id = %s ORDER BY created_at DESC",
            (patient_id,),
        )
        return [cls.from_row(r) for r in rows]
