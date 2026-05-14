"""Blood test domain model."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from laso.enums import BloodTestStatus
from laso.utils.db import execute, execute_one, insert

log = logging.getLogger(__name__)


@dataclass
class BloodTest:
    blood_test_id: str
    patient_id: str
    programme_id: str
    programme_step_id: Optional[str] = None
    status: BloodTestStatus = BloodTestStatus.ORDERED
    hba1c: Optional[float] = None
    fasting_glucose: Optional[float] = None
    total_cholesterol: Optional[float] = None
    ldl: Optional[float] = None
    hdl: Optional[float] = None
    triglycerides: Optional[float] = None
    tsh: Optional[float] = None
    creatinine: Optional[float] = None
    alt: Optional[float] = None
    ast: Optional[float] = None
    entered_by: Optional[str] = None
    ordered_at: Optional[datetime] = None
    results_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {k: (v.isoformat() if isinstance(v, datetime) else v.value if hasattr(v, 'value') else v)
                for k, v in self.__dict__.items() if v is not None}

    @classmethod
    def from_row(cls, row: Dict) -> "BloodTest":
        return cls(
            blood_test_id=row["blood_test_id"],
            patient_id=row["patient_id"],
            programme_id=row["programme_id"],
            programme_step_id=row.get("programme_step_id"),
            status=BloodTestStatus(row["status"]),
            hba1c=row.get("hba1c"),
            fasting_glucose=row.get("fasting_glucose"),
            total_cholesterol=row.get("total_cholesterol"),
            ldl=row.get("ldl"),
            hdl=row.get("hdl"),
            triglycerides=row.get("triglycerides"),
            tsh=row.get("tsh"),
            creatinine=row.get("creatinine"),
            alt=row.get("alt"),
            ast=row.get("ast"),
            entered_by=row.get("entered_by"),
            ordered_at=row.get("ordered_at"),
            results_at=row.get("results_at"),
        )

    def save(self) -> None:
        log.info("BloodTest.save | blood_test_id=%s", self.blood_test_id)
        insert(
            """INSERT INTO blood_tests (blood_test_id, patient_id, programme_id, programme_step_id,
               status, hba1c, fasting_glucose, total_cholesterol, ldl, hdl,
               triglycerides, tsh, creatinine, alt, ast, entered_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (self.blood_test_id, self.patient_id, self.programme_id, self.programme_step_id,
             self.status.value, self.hba1c, self.fasting_glucose, self.total_cholesterol,
             self.ldl, self.hdl, self.triglycerides, self.tsh,
             self.creatinine, self.alt, self.ast, self.entered_by),
        )

    @classmethod
    def get_by_id(cls, blood_test_id: str) -> Optional["BloodTest"]:
        row = execute_one("SELECT * FROM blood_tests WHERE blood_test_id = %s", (blood_test_id,))
        return cls.from_row(row) if row else None

    @classmethod
    def list_for_programme(cls, programme_id: str) -> List["BloodTest"]:
        rows = execute("SELECT * FROM blood_tests WHERE programme_id = %s ORDER BY ordered_at DESC", (programme_id,))
        return [cls.from_row(r) for r in rows]
