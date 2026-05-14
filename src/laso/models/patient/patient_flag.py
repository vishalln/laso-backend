"""Patient flag domain model."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from laso.enums import FlagType
from laso.utils.db import execute, execute_one, insert, update_by_id

log = logging.getLogger(__name__)


@dataclass
class PatientFlag:
    flag_id: str
    patient_id: str
    flag_type: FlagType
    reason: str
    created_by: str
    cleared_at: Optional[datetime] = None
    cleared_by: Optional[str] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "flag_id": self.flag_id,
            "patient_id": self.patient_id,
            "flag_type": self.flag_type.value,
            "reason": self.reason,
            "created_by": self.created_by,
            "cleared_at": self.cleared_at.isoformat() if self.cleared_at else None,
            "cleared_by": self.cleared_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_row(cls, row: Dict) -> "PatientFlag":
        return cls(
            flag_id=row["flag_id"],
            patient_id=row["patient_id"],
            flag_type=FlagType(row["flag_type"]),
            reason=row["reason"],
            created_by=row["created_by"],
            cleared_at=row.get("cleared_at"),
            cleared_by=row.get("cleared_by"),
            created_at=row.get("created_at"),
        )

    def save(self) -> None:
        log.info("PatientFlag.save | flag_id=%s", self.flag_id)
        insert(
            """INSERT INTO patient_flags (flag_id, patient_id, flag_type, reason, created_by)
               VALUES (%s,%s,%s,%s,%s)""",
            (self.flag_id, self.patient_id, self.flag_type.value, self.reason, self.created_by),
        )
        log.info("PatientFlag.save | success | flag_id=%s", self.flag_id)

    @classmethod
    def get_active_flags(cls, patient_id: str) -> List["PatientFlag"]:
        rows = execute(
            "SELECT * FROM patient_flags WHERE patient_id = %s AND cleared_at IS NULL ORDER BY created_at DESC",
            (patient_id,),
        )
        return [cls.from_row(r) for r in rows]

    @classmethod
    def clear(cls, flag_id: str, cleared_by: str) -> Optional["PatientFlag"]:
        update_by_id("patient_flags", "flag_id", flag_id, cleared_at=datetime.utcnow(), cleared_by=cleared_by)
        row = execute_one("SELECT * FROM patient_flags WHERE flag_id = %s", (flag_id,))
        return cls.from_row(row) if row else None
