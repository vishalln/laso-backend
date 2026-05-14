"""Clinical domain enumerations."""

from enum import Enum


class NoteType(str, Enum):
    PROGRESS = "progress"
    CLINICAL_REVIEW = "clinical_review"
    PRESCRIPTION_CHANGE = "prescription_change"
    ALERT = "alert"
    CONSULTATION_SUMMARY = "consultation_summary"


class FlagType(str, Enum):
    URGENT = "urgent"
    REVIEW_NEEDED = "review_needed"
    PLATEAU = "plateau"
    ADHERENCE_RISK = "adherence_risk"
