"""Weekly check-in domain model."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from psycopg2.extras import Json

from laso.utils.db import execute, execute_one, insert

log = logging.getLogger(__name__)


@dataclass
class WeeklyCheckIn:
    check_in_id: str
    patient_id: str
    programme_id: str
    programme_step_id: Optional[str] = None
    week_number: int = 1
    weight_kg: float = 0.0
    fasting_glucose: Optional[float] = None
    doses_taken: int = 0
    doses_scheduled: int = 0
    side_effects: list = field(default_factory=list)
    appetite_level: Optional[int] = None
    energy_level: Optional[int] = None
    notes: Optional[str] = None
    submitted_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "check_in_id": self.check_in_id,
            "patient_id": self.patient_id,
            "programme_id": self.programme_id,
            "programme_step_id": self.programme_step_id,
            "week_number": self.week_number,
            "weight_kg": self.weight_kg,
            "fasting_glucose": self.fasting_glucose,
            "doses_taken": self.doses_taken,
            "doses_scheduled": self.doses_scheduled,
            "side_effects": self.side_effects,
            "appetite_level": self.appetite_level,
            "energy_level": self.energy_level,
            "notes": self.notes,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
        }

    @classmethod
    def from_row(cls, row: Dict) -> "WeeklyCheckIn":
        return cls(
            check_in_id=row["check_in_id"],
            patient_id=row["patient_id"],
            programme_id=row["programme_id"],
            programme_step_id=row.get("programme_step_id"),
            week_number=row.get("week_number", 1),
            weight_kg=row.get("weight_kg", 0.0),
            fasting_glucose=row.get("fasting_glucose"),
            doses_taken=row.get("doses_taken", 0),
            doses_scheduled=row.get("doses_scheduled", 0),
            side_effects=row.get("side_effects") or [],
            appetite_level=row.get("appetite_level"),
            energy_level=row.get("energy_level"),
            notes=row.get("notes"),
            submitted_at=row.get("submitted_at"),
        )

    def save(self) -> None:
        log.info("WeeklyCheckIn.save | check_in_id=%s", self.check_in_id)
        insert(
            """INSERT INTO weekly_check_ins (check_in_id, patient_id, programme_id,
               programme_step_id, week_number, weight_kg, fasting_glucose, doses_taken,
               doses_scheduled, side_effects, appetite_level, energy_level, notes)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (self.check_in_id, self.patient_id, self.programme_id,
             self.programme_step_id, self.week_number, self.weight_kg,
             self.fasting_glucose, self.doses_taken, self.doses_scheduled,
             Json(self.side_effects), self.appetite_level, self.energy_level,
             self.notes),
        )
        log.info("WeeklyCheckIn.save | success | check_in_id=%s", self.check_in_id)

    @classmethod
    def get_by_id(cls, check_in_id: str) -> Optional["WeeklyCheckIn"]:
        row = execute_one("SELECT * FROM weekly_check_ins WHERE check_in_id = %s", (check_in_id,))
        return cls.from_row(row) if row else None

    @classmethod
    def list_for_programme(cls, programme_id: str) -> List["WeeklyCheckIn"]:
        rows = execute(
            "SELECT * FROM weekly_check_ins WHERE programme_id = %s ORDER BY week_number ASC",
            (programme_id,),
        )
        return [cls.from_row(r) for r in rows]

    @classmethod
    def get_latest(cls, patient_id: str) -> Optional["WeeklyCheckIn"]:
        row = execute_one(
            "SELECT * FROM weekly_check_ins WHERE patient_id = %s ORDER BY submitted_at DESC LIMIT 1",
            (patient_id,),
        )
        return cls.from_row(row) if row else None
