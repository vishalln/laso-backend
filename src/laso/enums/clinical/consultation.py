"""Consultation domain enumerations."""

from enum import Enum


class ConsultationStatus(str, Enum):
    NEEDS_SCHEDULING = "needs_scheduling"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    CANCELLED = "cancelled"

    @classmethod
    def valid_transitions(cls) -> dict:
        return {
            cls.NEEDS_SCHEDULING: [cls.SCHEDULED, cls.CANCELLED],
            cls.SCHEDULED: [cls.IN_PROGRESS, cls.NO_SHOW, cls.CANCELLED],
            cls.IN_PROGRESS: [cls.COMPLETED],
            cls.COMPLETED: [],
            cls.NO_SHOW: [cls.NEEDS_SCHEDULING],
            cls.CANCELLED: [],
        }


class ConsultationType(str, Enum):
    INITIAL = "initial"
    FOLLOW_UP = "follow_up"
    DOSE_REVIEW = "dose_review"
