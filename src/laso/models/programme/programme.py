"""Programme domain models."""

import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, List, Optional

from laso.enums import ProgrammeStatus, StepStatus, StepType, AutoActivateRule
from laso.utils.db import execute, execute_one, insert

log = logging.getLogger(__name__)


@dataclass
class Programme:
    programme_id: str
    patient_id: str
    doctor_id: str
    template_id: str
    template_version: int
    name: str
    status: ProgrammeStatus = ProgrammeStatus.CREATED
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    paused_at_step_id: Optional[str] = None
    pause_reason: Optional[str] = None
    cancel_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "programme_id": self.programme_id,
            "patient_id": self.patient_id,
            "doctor_id": self.doctor_id,
            "template_id": self.template_id,
            "template_version": self.template_version,
            "name": self.name,
            "status": self.status.value,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "paused_at_step_id": self.paused_at_step_id,
            "pause_reason": self.pause_reason,
            "cancel_reason": self.cancel_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_row(cls, row: Dict) -> "Programme":
        return cls(
            programme_id=row["programme_id"],
            patient_id=row["patient_id"],
            doctor_id=row["doctor_id"],
            template_id=row["template_id"],
            template_version=row["template_version"],
            name=row["name"],
            status=ProgrammeStatus(row["status"]),
            start_date=row.get("start_date"),
            end_date=row.get("end_date"),
            paused_at_step_id=row.get("paused_at_step_id"),
            pause_reason=row.get("pause_reason"),
            cancel_reason=row.get("cancel_reason"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def save(self) -> None:
        log.info("Programme.save | programme_id=%s", self.programme_id)
        insert(
            """INSERT INTO programmes (programme_id, patient_id, doctor_id, template_id,
               template_version, name, status, start_date, end_date,
               paused_at_step_id, pause_reason, cancel_reason)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (self.programme_id, self.patient_id, self.doctor_id, self.template_id,
             self.template_version, self.name, self.status.value, self.start_date,
             self.end_date, self.paused_at_step_id, self.pause_reason, self.cancel_reason),
        )
        log.info("Programme.save | success | programme_id=%s", self.programme_id)

    @classmethod
    def get_by_id(cls, programme_id: str) -> Optional["Programme"]:
        row = execute_one("SELECT * FROM programmes WHERE programme_id = %s", (programme_id,))
        return cls.from_row(row) if row else None

    @classmethod
    def get_active(cls, patient_id: str) -> Optional["Programme"]:
        row = execute_one(
            "SELECT * FROM programmes WHERE patient_id = %s AND status = 'active' LIMIT 1",
            (patient_id,),
        )
        return cls.from_row(row) if row else None

    @classmethod
    def list_for_patient(cls, patient_id: str) -> List["Programme"]:
        rows = execute(
            "SELECT * FROM programmes WHERE patient_id = %s ORDER BY created_at DESC",
            (patient_id,),
        )
        return [cls.from_row(r) for r in rows]


@dataclass
class ProgrammeStep:
    step_id: str
    programme_id: str
    template_step_id: Optional[str]
    title: str
    step_type: StepType
    week_offset: int = 0
    duration_minutes: int = 0
    is_recurring: bool = False
    auto_activate_rule: AutoActivateRule = AutoActivateRule.MANUAL
    is_flagged: bool = False
    status: StepStatus = StepStatus.PENDING
    sort_order: int = 0
    activated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    skip_reason: Optional[str] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "step_id": self.step_id,
            "programme_id": self.programme_id,
            "template_step_id": self.template_step_id,
            "title": self.title,
            "step_type": self.step_type.value,
            "week_offset": self.week_offset,
            "duration_minutes": self.duration_minutes,
            "is_recurring": self.is_recurring,
            "auto_activate_rule": self.auto_activate_rule.value,
            "is_flagged": self.is_flagged,
            "status": self.status.value,
            "sort_order": self.sort_order,
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "skip_reason": self.skip_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_row(cls, row: Dict) -> "ProgrammeStep":
        return cls(
            step_id=row["step_id"],
            programme_id=row["programme_id"],
            template_step_id=row.get("template_step_id"),
            title=row["title"],
            step_type=StepType(row["step_type"]),
            week_offset=row.get("week_offset", 0),
            duration_minutes=row.get("duration_minutes", 0),
            is_recurring=row.get("is_recurring", False),
            auto_activate_rule=AutoActivateRule(row.get("auto_activate_rule", "manual")),
            is_flagged=row.get("is_flagged", False),
            status=StepStatus(row.get("status", "pending")),
            sort_order=row.get("sort_order", 0),
            activated_at=row.get("activated_at"),
            completed_at=row.get("completed_at"),
            skip_reason=row.get("skip_reason"),
            created_at=row.get("created_at"),
        )

    def save(self) -> None:
        log.info("ProgrammeStep.save | step_id=%s", self.step_id)
        insert(
            """INSERT INTO programme_steps (step_id, programme_id, template_step_id, title,
               step_type, week_offset, duration_minutes, is_recurring, auto_activate_rule,
               is_flagged, status, sort_order, activated_at, completed_at, skip_reason)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (self.step_id, self.programme_id, self.template_step_id, self.title,
             self.step_type.value, self.week_offset, self.duration_minutes,
             self.is_recurring, self.auto_activate_rule.value, self.is_flagged,
             self.status.value, self.sort_order, self.activated_at, self.completed_at,
             self.skip_reason),
        )

    @classmethod
    def list_for_programme(cls, programme_id: str) -> List["ProgrammeStep"]:
        rows = execute(
            "SELECT * FROM programme_steps WHERE programme_id = %s ORDER BY sort_order",
            (programme_id,),
        )
        return [cls.from_row(r) for r in rows]

    @classmethod
    def get_active_step(cls, programme_id: str) -> Optional["ProgrammeStep"]:
        row = execute_one(
            "SELECT * FROM programme_steps WHERE programme_id = %s AND status = 'active' ORDER BY sort_order LIMIT 1",
            (programme_id,),
        )
        return cls.from_row(row) if row else None

    @classmethod
    def get_by_id(cls, step_id: str) -> Optional["ProgrammeStep"]:
        row = execute_one("SELECT * FROM programme_steps WHERE step_id = %s", (step_id,))
        return cls.from_row(row) if row else None

    @classmethod
    def create_from_template(cls, programme_id: str, template_id: str) -> List["ProgrammeStep"]:
        """Copy all steps from protocol_template_steps for template_id into programme_steps."""
        from uuid import uuid4
        from laso.models.protocol import ProtocolTemplateStep

        template_steps = ProtocolTemplateStep.list_for_template(template_id)
        created_steps = []
        for ts in template_steps:
            step = cls(
                step_id=str(uuid4()),
                programme_id=programme_id,
                template_step_id=ts.step_id,
                title=ts.title,
                step_type=ts.step_type,
                week_offset=ts.week_offset,
                duration_minutes=ts.duration_minutes,
                is_recurring=ts.is_recurring,
                auto_activate_rule=ts.auto_activate_rule,
                is_flagged=ts.is_flagged,
                status=StepStatus.PENDING,
                sort_order=ts.sort_order,
            )
            step.save()
            created_steps.append(step)
        log.info("ProgrammeStep.create_from_template | programme_id=%s count=%d", programme_id, len(created_steps))
        return created_steps
