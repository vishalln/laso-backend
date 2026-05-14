"""Order domain enumerations."""

from enum import Enum


class OrderStatus(str, Enum):
    DISPENSED = "dispensed"
    PACKED = "packed"
    COLD_CHAIN_VERIFIED = "cold_chain_verified"
    COLD_CHAIN_FAILED = "cold_chain_failed"
    DISPATCHED = "dispatched"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"

    @classmethod
    def valid_transitions(cls) -> dict:
        """Strictly linear — no skipping steps."""
        return {
            cls.DISPENSED: [cls.PACKED],
            cls.PACKED: [cls.COLD_CHAIN_VERIFIED, cls.COLD_CHAIN_FAILED],
            cls.COLD_CHAIN_VERIFIED: [cls.DISPATCHED],
            cls.COLD_CHAIN_FAILED: [],
            cls.DISPATCHED: [cls.IN_TRANSIT],
            cls.IN_TRANSIT: [cls.DELIVERED],
            cls.DELIVERED: [],
        }


class ColdChainStatus(str, Enum):
    PENDING = "pending"
    PASS = "pass"
    FAIL = "fail"
