"""Blood test domain enumerations."""

from enum import Enum


class BloodTestStatus(str, Enum):
    ORDERED = "ordered"
    RESULTS_READY = "results_ready"

    @classmethod
    def valid_transitions(cls) -> dict:
        return {
            cls.ORDERED: [cls.RESULTS_READY],
            cls.RESULTS_READY: [],
        }
