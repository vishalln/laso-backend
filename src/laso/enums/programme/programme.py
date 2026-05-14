"""Programme domain enumerations."""

from enum import Enum


class ProgrammeStatus(str, Enum):
    CREATED = "created"
    PAYMENT_PENDING = "payment_pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    @classmethod
    def valid_transitions(cls) -> dict:
        return {
            cls.CREATED: [cls.PAYMENT_PENDING],
            cls.PAYMENT_PENDING: [cls.ACTIVE],
            cls.ACTIVE: [cls.PAUSED, cls.COMPLETED, cls.CANCELLED],
            cls.PAUSED: [cls.ACTIVE, cls.CANCELLED],
            cls.COMPLETED: [],
            cls.CANCELLED: [],
        }


class StepStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    SKIPPED = "skipped"

    @classmethod
    def valid_transitions(cls) -> dict:
        return {
            cls.PENDING: [cls.ACTIVE, cls.SKIPPED],
            cls.ACTIVE: [cls.COMPLETED, cls.SKIPPED, cls.PENDING],
            cls.COMPLETED: [],
            cls.SKIPPED: [],
        }


class StepType(str, Enum):
    BLOOD_TEST = "blood_test"
    CONSULTATION = "consultation"
    PRESCRIPTION = "prescription"
    CHECK_IN = "check_in"
    DOSE_REVIEW = "dose_review"
    LAB_TEST = "lab_test"
    OTHER = "other"


class AutoActivateRule(str, Enum):
    PREVIOUS_COMPLETE = "previous_complete"
    MANUAL = "manual"
    ON_PROGRAMME_START = "on_programme_start"
