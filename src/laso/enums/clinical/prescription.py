"""Prescription domain enumerations."""

from enum import Enum


class PrescriptionStatus(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    CANCELLED = "cancelled"

    @classmethod
    def valid_transitions(cls) -> dict:
        return {
            cls.ACTIVE: [cls.SUPERSEDED, cls.CANCELLED],
            cls.SUPERSEDED: [],
            cls.CANCELLED: [],
        }
