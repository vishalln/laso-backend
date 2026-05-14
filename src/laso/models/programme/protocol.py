"""Protocol template domain models."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from laso.enums import StepType, AutoActivateRule
from laso.utils.db import execute, execute_one, insert

log = logging.getLogger(__name__)


@dataclass
class ProtocolTemplate:
    template_id: str
    name: str
    description: Optional[str] = None
    total_weeks: int = 0
    version: int = 1
    status: str = "draft"
    published_at: Optional[datetime] = None
    published_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "total_weeks": self.total_weeks,
            "version": self.version,
            "status": self.status,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "published_by": self.published_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_row(cls, row: Dict) -> "ProtocolTemplate":
        return cls(
            template_id=row["template_id"],
            name=row["name"],
            description=row.get("description"),
            total_weeks=row.get("total_weeks", 0),
            version=row.get("version", 1),
            status=row.get("status", "draft"),
            published_at=row.get("published_at"),
            published_by=row.get("published_by"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def save(self) -> None:
        log.info("ProtocolTemplate.save | template_id=%s", self.template_id)
        insert(
            """INSERT INTO protocol_templates (template_id, name, description, total_weeks,
               version, status, published_at, published_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (self.template_id, self.name, self.description, self.total_weeks,
             self.version, self.status, self.published_at, self.published_by),
        )
        log.info("ProtocolTemplate.save | success | template_id=%s", self.template_id)

    @classmethod
    def get_by_id(cls, template_id: str) -> Optional["ProtocolTemplate"]:
        row = execute_one("SELECT * FROM protocol_templates WHERE template_id = %s", (template_id,))
        return cls.from_row(row) if row else None

    @classmethod
    def get_published(cls) -> Optional["ProtocolTemplate"]:
        row = execute_one(
            "SELECT * FROM protocol_templates WHERE status = 'published' ORDER BY version DESC LIMIT 1"
        )
        return cls.from_row(row) if row else None


@dataclass
class ProtocolTemplateStep:
    step_id: str
    template_id: str
    title: str
    step_type: StepType
    week_offset: int = 0
    duration_minutes: int = 0
    is_recurring: bool = False
    auto_activate_rule: AutoActivateRule = AutoActivateRule.MANUAL
    is_flagged: bool = False
    sort_order: int = 0
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "step_id": self.step_id,
            "template_id": self.template_id,
            "title": self.title,
            "step_type": self.step_type.value,
            "week_offset": self.week_offset,
            "duration_minutes": self.duration_minutes,
            "is_recurring": self.is_recurring,
            "auto_activate_rule": self.auto_activate_rule.value,
            "is_flagged": self.is_flagged,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_row(cls, row: Dict) -> "ProtocolTemplateStep":
        return cls(
            step_id=row["step_id"],
            template_id=row["template_id"],
            title=row["title"],
            step_type=StepType(row["step_type"]),
            week_offset=row.get("week_offset", 0),
            duration_minutes=row.get("duration_minutes", 0),
            is_recurring=row.get("is_recurring", False),
            auto_activate_rule=AutoActivateRule(row.get("auto_activate_rule", "manual")),
            is_flagged=row.get("is_flagged", False),
            sort_order=row.get("sort_order", 0),
            created_at=row.get("created_at"),
        )

    def save(self) -> None:
        log.info("ProtocolTemplateStep.save | step_id=%s", self.step_id)
        insert(
            """INSERT INTO protocol_template_steps (step_id, template_id, title, step_type,
               week_offset, duration_minutes, is_recurring, auto_activate_rule, is_flagged, sort_order)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (self.step_id, self.template_id, self.title, self.step_type.value,
             self.week_offset, self.duration_minutes, self.is_recurring,
             self.auto_activate_rule.value, self.is_flagged, self.sort_order),
        )

    @classmethod
    def list_for_template(cls, template_id: str) -> List["ProtocolTemplateStep"]:
        rows = execute(
            "SELECT * FROM protocol_template_steps WHERE template_id = %s ORDER BY sort_order",
            (template_id,),
        )
        return [cls.from_row(r) for r in rows]


@dataclass
class ProtocolTemplateVersion:
    id: str
    template_id: str
    version: int
    published_at: Optional[datetime] = None
    published_by: Optional[str] = None
    step_count: int = 0
    steps_snapshot: Optional[list] = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "template_id": self.template_id,
            "version": self.version,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "published_by": self.published_by,
            "step_count": self.step_count,
            "steps_snapshot": self.steps_snapshot,
        }

    @classmethod
    def from_row(cls, row: Dict) -> "ProtocolTemplateVersion":
        return cls(
            id=row["id"],
            template_id=row["template_id"],
            version=row["version"],
            published_at=row.get("published_at"),
            published_by=row.get("published_by"),
            step_count=row.get("step_count", 0),
            steps_snapshot=row.get("steps_snapshot"),
        )

    def save(self) -> None:
        log.info("ProtocolTemplateVersion.save | id=%s version=%s", self.id, self.version)
        insert(
            """INSERT INTO protocol_template_versions (id, template_id, version, published_at,
               published_by, step_count, steps_snapshot)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (self.id, self.template_id, self.version, self.published_at,
             self.published_by, self.step_count,
             __import__("json").dumps(self.steps_snapshot) if self.steps_snapshot else None),
        )

    @classmethod
    def list_for_template(cls, template_id: str) -> List["ProtocolTemplateVersion"]:
        rows = execute(
            "SELECT * FROM protocol_template_versions WHERE template_id = %s ORDER BY version DESC",
            (template_id,),
        )
        return [cls.from_row(r) for r in rows]
