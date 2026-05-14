"""Doctor domain models."""

import logging
from dataclasses import dataclass
from datetime import datetime, time
from typing import Dict, List, Optional

from laso.enums import DoctorSpecialisation
from laso.utils.db import execute, execute_one, insert

log = logging.getLogger(__name__)


@dataclass
class Doctor:
    doctor_id: str
    email: str
    name: str
    specialisation: DoctorSpecialisation
    phone: Optional[str] = None
    status: str = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "doctor_id": self.doctor_id,
            "email": self.email,
            "name": self.name,
            "specialisation": self.specialisation.value,
            "phone": self.phone,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_row(cls, row: Dict) -> "Doctor":
        return cls(
            doctor_id=row["doctor_id"],
            email=row["email"],
            name=row["name"],
            specialisation=DoctorSpecialisation(row["specialisation"]),
            phone=row.get("phone"),
            status=row.get("status", "active"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def save(self) -> None:
        log.info("Doctor.save | doctor_id=%s", self.doctor_id)
        insert(
            """INSERT INTO doctors (doctor_id, email, name, specialisation, phone, status)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            (self.doctor_id, self.email, self.name, self.specialisation.value,
             self.phone, self.status),
        )
        log.info("Doctor.save | success | doctor_id=%s", self.doctor_id)

    @classmethod
    def get_by_id(cls, doctor_id: str) -> Optional["Doctor"]:
        row = execute_one("SELECT * FROM doctors WHERE doctor_id = %s", (doctor_id,))
        return cls.from_row(row) if row else None

    @classmethod
    def list_all(cls) -> List["Doctor"]:
        rows = execute("SELECT * FROM doctors ORDER BY name")
        return [cls.from_row(r) for r in rows]


@dataclass
class DoctorWorkingHours:
    id: str
    doctor_id: str
    day_of_week: int
    is_working: bool
    start_time: Optional[time] = None
    end_time: Optional[time] = None

    @classmethod
    def from_row(cls, row: Dict) -> "DoctorWorkingHours":
        return cls(
            id=row["id"],
            doctor_id=row["doctor_id"],
            day_of_week=row["day_of_week"],
            is_working=row["is_working"],
            start_time=row.get("start_time"),
            end_time=row.get("end_time"),
        )

    def save(self) -> None:
        log.info("DoctorWorkingHours.save | id=%s doctor_id=%s", self.id, self.doctor_id)
        insert(
            """INSERT INTO doctor_working_hours (id, doctor_id, day_of_week, is_working, start_time, end_time)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            (self.id, self.doctor_id, self.day_of_week, self.is_working,
             self.start_time, self.end_time),
        )

    @classmethod
    def get_for_doctor(cls, doctor_id: str) -> List["DoctorWorkingHours"]:
        rows = execute(
            "SELECT * FROM doctor_working_hours WHERE doctor_id = %s ORDER BY day_of_week",
            (doctor_id,),
        )
        return [cls.from_row(r) for r in rows]
