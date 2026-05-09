"""Quiz submission data model — OO persistence via save()."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Optional

from laso.constants.sql import QuizSQL
from laso.utils.db import insert

log = logging.getLogger(__name__)


@dataclass
class QuizSubmission:
    quiz_id:             str = field(default_factory=lambda: str(uuid.uuid4()))
    age:                 Optional[int] = None
    gender:              Optional[str] = None
    height_cm:           Optional[float] = None
    weight_kg:           Optional[float] = None
    conditions:          list[str] = field(default_factory=list)
    current_medications: list[str] = field(default_factory=list)
    symptoms:            list[str] = field(default_factory=list)
    activity_level:      Optional[str] = None
    diet_type:           Optional[str] = None
    sleep_hours:         Optional[float] = None
    stress_level:        Optional[int] = None
    primary_goal:        Optional[str] = None
    target_weight_kg:    Optional[float] = None
    timeline_weeks:      Optional[str] = None
    readiness_score:     Optional[int] = None
    main_concern:        Optional[str] = None
    bmi:                 Optional[float] = None
    eligible:            Optional[bool] = None

    @classmethod
    def from_dict(cls, data: dict) -> "QuizSubmission":
        """Construct from camelCase API payload."""
        return cls(
            age=data.get("age"),
            gender=data.get("gender"),
            height_cm=data.get("heightCm"),
            weight_kg=data.get("weightKg"),
            conditions=data.get("conditions", []),
            current_medications=data.get("currentMedications", []),
            symptoms=data.get("symptoms", []),
            activity_level=data.get("activityLevel"),
            diet_type=data.get("dietType"),
            sleep_hours=data.get("sleepHours"),
            stress_level=data.get("stressLevel"),
            primary_goal=data.get("primaryGoal"),
            target_weight_kg=data.get("targetWeightKg"),
            timeline_weeks=data.get("timelineWeeks"),
            readiness_score=data.get("readinessScore"),
            main_concern=data.get("mainConcern"),
        )

    def to_params(self) -> tuple:
        """Serialize to SQL parameter tuple matching QuizSQL.INSERT column order."""
        return (
            self.quiz_id, self.age, self.gender,
            self.height_cm, self.weight_kg,
            self.conditions, self.current_medications, self.symptoms,
            self.activity_level, self.diet_type, self.sleep_hours, self.stress_level,
            self.primary_goal, self.target_weight_kg, self.timeline_weeks,
            self.readiness_score, self.main_concern, self.bmi, self.eligible,
        )

    def save(self) -> None:
        """Persist to PostgreSQL."""
        log.info("QuizSubmission.save | quiz_id=%s", self.quiz_id)
        insert(QuizSQL.INSERT, self.to_params())
        log.info("QuizSubmission.save | success | quiz_id=%s", self.quiz_id)
