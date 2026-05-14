"""Payment domain enumerations."""

from enum import Enum


class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

    @classmethod
    def valid_transitions(cls) -> dict:
        return {
            cls.PENDING: [cls.COMPLETED, cls.FAILED],
            cls.COMPLETED: [cls.REFUNDED],
            cls.FAILED: [cls.PENDING],
            cls.REFUNDED: [],
        }
