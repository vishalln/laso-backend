"""Task domain enumerations."""

from enum import Enum


class TaskType(str, Enum):
    SCHEDULE_CONSULTATION = "schedule_consultation"
    MISSED_CHECK_IN = "missed_check_in"
    REFILL_REQUEST = "refill_request"
    ENTER_BLOOD_RESULTS = "enter_blood_results"
    CREATE_ORDER = "create_order"
    ESCALATION = "escalation"
    FOLLOW_UP = "follow_up"
    RESCHEDULE_NO_SHOW = "reschedule_no_show"


class TaskPriority(str, Enum):
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(str, Enum):
    PENDING = "pending"
    DONE = "done"
    ARCHIVED = "archived"

    @classmethod
    def valid_transitions(cls) -> dict:
        return {
            cls.PENDING: [cls.DONE, cls.ARCHIVED],
            cls.DONE: [cls.ARCHIVED],
            cls.ARCHIVED: [],
        }
