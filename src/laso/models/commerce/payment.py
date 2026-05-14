"""Payment domain model."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

from laso.enums import PaymentStatus
from laso.utils.db import execute_one, insert

log = logging.getLogger(__name__)


@dataclass
class Payment:
    payment_id: str
    programme_id: str
    patient_id: str
    amount: float
    currency: str = "INR"
    status: PaymentStatus = PaymentStatus.PENDING
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "payment_id": self.payment_id,
            "programme_id": self.programme_id,
            "patient_id": self.patient_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_row(cls, row: Dict) -> "Payment":
        return cls(
            payment_id=row["payment_id"],
            programme_id=row["programme_id"],
            patient_id=row["patient_id"],
            amount=row["amount"],
            currency=row.get("currency", "INR"),
            status=PaymentStatus(row["status"]),
            created_at=row.get("created_at"),
            completed_at=row.get("completed_at"),
        )

    def save(self) -> None:
        log.info("Payment.save | payment_id=%s", self.payment_id)
        insert(
            """INSERT INTO payments (payment_id, programme_id, patient_id, amount, currency, status)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            (self.payment_id, self.programme_id, self.patient_id, self.amount,
             self.currency, self.status.value),
        )
        log.info("Payment.save | success | payment_id=%s", self.payment_id)

    @classmethod
    def get_by_id(cls, payment_id: str) -> Optional["Payment"]:
        row = execute_one("SELECT * FROM payments WHERE payment_id = %s", (payment_id,))
        return cls.from_row(row) if row else None
