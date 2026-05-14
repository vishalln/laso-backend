"""Treatment plan domain model."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

from laso.utils.db import execute_one, insert, update_by_id

log = logging.getLogger(__name__)


@dataclass
class TreatmentPlan:
    plan_id: str
    patient_id: str
    programme_id: str
    doctor_id: str
    diagnosis_notes: Optional[str] = None
    target_dose: Optional[float] = None
    target_dose_unit: Optional[str] = None
    titration_schedule: Optional[str] = None
    diet_guidelines: Optional[str] = None
    activity_target: Optional[str] = None
    weight_target_kg: Optional[float] = None
    glucose_target: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "plan_id": self.plan_id,
            "patient_id": self.patient_id,
            "programme_id": self.programme_id,
            "doctor_id": self.doctor_id,
            "diagnosis_notes": self.diagnosis_notes,
            "target_dose": self.target_dose,
            "target_dose_unit": self.target_dose_unit,
            "titration_schedule": self.titration_schedule,
            "diet_guidelines": self.diet_guidelines,
            "activity_target": self.activity_target,
            "weight_target_kg": self.weight_target_kg,
            "glucose_target": self.glucose_target,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_row(cls, row: Dict) -> "TreatmentPlan":
        return cls(
            plan_id=row["plan_id"],
            patient_id=row["patient_id"],
            programme_id=row["programme_id"],
            doctor_id=row["doctor_id"],
            diagnosis_notes=row.get("diagnosis_notes"),
            target_dose=row.get("target_dose"),
            target_dose_unit=row.get("target_dose_unit"),
            titration_schedule=row.get("titration_schedule"),
            diet_guidelines=row.get("diet_guidelines"),
            activity_target=row.get("activity_target"),
            weight_target_kg=row.get("weight_target_kg"),
            glucose_target=row.get("glucose_target"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def save(self) -> None:
        log.info("TreatmentPlan.save | plan_id=%s", self.plan_id)
        insert(
            """INSERT INTO treatment_plans (plan_id, patient_id, programme_id, doctor_id,
               diagnosis_notes, target_dose, target_dose_unit, titration_schedule,
               diet_guidelines, activity_target, weight_target_kg, glucose_target)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (self.plan_id, self.patient_id, self.programme_id, self.doctor_id,
             self.diagnosis_notes, self.target_dose, self.target_dose_unit,
             self.titration_schedule, self.diet_guidelines, self.activity_target,
             self.weight_target_kg, self.glucose_target),
        )

    @classmethod
    def get_for_programme(cls, programme_id: str) -> Optional["TreatmentPlan"]:
        row = execute_one(
            "SELECT * FROM treatment_plans WHERE programme_id = %s", (programme_id,)
        )
        return cls.from_row(row) if row else None

    @classmethod
    def update(cls, programme_id: str, fields: dict) -> Optional["TreatmentPlan"]:
        update_by_id("treatment_plans", "programme_id", programme_id, **fields)
        return cls.get_for_programme(programme_id)
