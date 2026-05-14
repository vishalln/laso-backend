"""Patient domain model."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from laso.enums import UserStatus
from laso.utils.db import execute, execute_one, insert

log = logging.getLogger(__name__)


@dataclass
class Patient:
    patient_id: str
    email: str
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    city: Optional[str] = None
    height_cm: Optional[float] = None
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_pincode: Optional[str] = None
    status: UserStatus = UserStatus.ACTIVE
    assigned_doctor_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "patient_id": self.patient_id,
            "email": self.email,
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "city": self.city,
            "height_cm": self.height_cm,
            "phone": self.phone,
            "address_line1": self.address_line1,
            "address_line2": self.address_line2,
            "address_city": self.address_city,
            "address_state": self.address_state,
            "address_pincode": self.address_pincode,
            "status": self.status.value,
            "assigned_doctor_id": self.assigned_doctor_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_row(cls, row: Dict) -> "Patient":
        return cls(
            patient_id=row["patient_id"],
            email=row["email"],
            name=row["name"],
            age=row.get("age"),
            gender=row.get("gender"),
            city=row.get("city"),
            height_cm=row.get("height_cm"),
            phone=row.get("phone"),
            address_line1=row.get("address_line1"),
            address_line2=row.get("address_line2"),
            address_city=row.get("address_city"),
            address_state=row.get("address_state"),
            address_pincode=row.get("address_pincode"),
            status=UserStatus(row["status"]),
            assigned_doctor_id=row.get("assigned_doctor_id"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def save(self) -> None:
        log.info("Patient.save | patient_id=%s", self.patient_id)
        insert(
            """INSERT INTO patients (patient_id, email, name, age, gender, city, height_cm,
               phone, address_line1, address_line2, address_city, address_state, address_pincode,
               status, assigned_doctor_id)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (self.patient_id, self.email, self.name, self.age, self.gender, self.city,
             self.height_cm, self.phone, self.address_line1, self.address_line2,
             self.address_city, self.address_state, self.address_pincode,
             self.status.value, self.assigned_doctor_id),
        )
        log.info("Patient.save | success | patient_id=%s", self.patient_id)

    @classmethod
    def get_by_id(cls, patient_id: str) -> Optional["Patient"]:
        row = execute_one("SELECT * FROM patients WHERE patient_id = %s", (patient_id,))
        return cls.from_row(row) if row else None

    @classmethod
    def get_by_email(cls, email: str) -> Optional["Patient"]:
        row = execute_one("SELECT * FROM patients WHERE email = %s", (email,))
        return cls.from_row(row) if row else None

    @classmethod
    def list_for_doctor(cls, doctor_id: str) -> List["Patient"]:
        rows = execute("SELECT * FROM patients WHERE assigned_doctor_id = %s", (doctor_id,))
        return [cls.from_row(r) for r in rows]
