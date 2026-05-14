"""Quiz submission data model — persistence and hydration."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from laso.constants.sql import QuizSQL
from laso.utils.db import execute_one, insert

log = logging.getLogger(__name__)


@dataclass
class QuizSubmission:
    quiz_id:             str = field(default_factory=lambda: str(uuid.uuid4()))
    patient_id:          Optional[str] = None
    created_at:          Optional[datetime] = None
    age:                 Optional[int] = None
    gender:              Optional[str] = None
    height_cm:           Optional[float] = None
    weight_kg:           Optional[float] = None
    conditions:          List[str] = field(default_factory=list)
    current_medications: List[str] = field(default_factory=list)
    symptoms:            List[str] = field(default_factory=list)
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

    @classmethod
    def from_row(cls, row: Dict) -> "QuizSubmission":
        return cls(
            quiz_id=row["quiz_id"],
            patient_id=row.get("patient_id"),
            created_at=row.get("created_at"),
            age=row.get("age"),
            gender=row.get("gender"),
            height_cm=row.get("height_cm"),
            weight_kg=row.get("weight_kg"),
            conditions=row.get("conditions") or [],
            current_medications=row.get("current_medications") or [],
            symptoms=row.get("symptoms") or [],
            activity_level=row.get("activity_level"),
            diet_type=row.get("diet_type"),
            sleep_hours=row.get("sleep_hours"),
            stress_level=row.get("stress_level"),
            primary_goal=row.get("primary_goal"),
            target_weight_kg=row.get("target_weight_kg"),
            timeline_weeks=row.get("timeline_weeks"),
            readiness_score=row.get("readiness_score"),
            main_concern=row.get("main_concern"),
            bmi=row.get("bmi"),
            eligible=row.get("eligible"),
        )

    @classmethod
    def get_by_id(cls, quiz_id: str) -> Optional["QuizSubmission"]:
        log.info("QuizSubmission.get_by_id | quiz_id=%s", quiz_id)
        row = execute_one(QuizSQL.GET_BY_ID, (quiz_id,))
        return cls.from_row(row) if row else None

    @classmethod
    def get_latest_by_patient(cls, patient_id: str) -> Optional["QuizSubmission"]:
        log.info("QuizSubmission.get_latest_by_patient | patient_id=%s", patient_id)
        row = execute_one(QuizSQL.GET_LATEST_BY_PATIENT, (patient_id,))
        return cls.from_row(row) if row else None

    def claim(self, patient_id: str) -> bool:
        log.info("QuizSubmission.claim | quiz_id=%s patient_id=%s", self.quiz_id, patient_id)
        row = execute_one(QuizSQL.CLAIM, (patient_id, self.quiz_id))
        if row:
            self.patient_id = patient_id
            log.info("QuizSubmission.claim | success | quiz_id=%s", self.quiz_id)
            return True
        log.warning("QuizSubmission.claim | failed | quiz_id=%s", self.quiz_id)
        return False

    def to_dict(self) -> Dict:
        return {
            "quiz_id": self.quiz_id,
            "patient_id": self.patient_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "age": self.age,
            "gender": self.gender,
            "height_cm": self.height_cm,
            "weight_kg": self.weight_kg,
            "conditions": self.conditions,
            "current_medications": self.current_medications,
            "symptoms": self.symptoms,
            "activity_level": self.activity_level,
            "diet_type": self.diet_type,
            "sleep_hours": self.sleep_hours,
            "stress_level": self.stress_level,
            "primary_goal": self.primary_goal,
            "target_weight_kg": self.target_weight_kg,
            "timeline_weeks": self.timeline_weeks,
            "readiness_score": self.readiness_score,
            "main_concern": self.main_concern,
            "bmi": self.bmi,
            "eligible": self.eligible,
        }

    def to_params(self) -> tuple:
        return (
            self.quiz_id, self.patient_id,
            self.age, self.gender,
            self.height_cm, self.weight_kg,
            self.conditions, self.current_medications, self.symptoms,
            self.activity_level, self.diet_type, self.sleep_hours, self.stress_level,
            self.primary_goal, self.target_weight_kg, self.timeline_weeks,
            self.readiness_score, self.main_concern, self.bmi, self.eligible,
        )

    def save(self) -> None:
        log.info("QuizSubmission.save | quiz_id=%s patient_id=%s", self.quiz_id, self.patient_id)
        insert(QuizSQL.INSERT, self.to_params())
        log.info("QuizSubmission.save | success | quiz_id=%s", self.quiz_id)
