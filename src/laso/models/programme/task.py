"""Task domain model."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from laso.enums.task import TaskStatus, TaskPriority
from laso.utils.db import execute, execute_one, insert
from laso.utils.pagination import build_paginated_query, encode_cursor

log = logging.getLogger(__name__)


@dataclass
class Task:
    task_id: str
    patient_id: str
    task_type: str
    title: str
    priority: str
    status: TaskStatus = TaskStatus.PENDING
    due_date: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_to_doctor: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "patient_id": self.patient_id,
            "task_type": self.task_type,
            "title": self.title,
            "priority": self.priority if isinstance(self.priority, str) else self.priority.value,
            "status": self.status.value if isinstance(self.status, TaskStatus) else self.status,
            "due_date": self.due_date,
            "assigned_to": self.assigned_to,
            "assigned_to_doctor": self.assigned_to_doctor,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_row(cls, row: Dict) -> "Task":
        return cls(
            task_id=row["task_id"],
            patient_id=row["patient_id"],
            task_type=row["task_type"],
            title=row["title"],
            priority=row.get("priority", "medium"),
            status=TaskStatus(row.get("status", "pending")),
            due_date=row.get("due_date"),
            assigned_to=row.get("assigned_to"),
            assigned_to_doctor=row.get("assigned_to_doctor"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def save(self) -> None:
        log.info("Task.save | task_id=%s", self.task_id)
        status_val = self.status.value if isinstance(self.status, TaskStatus) else self.status
        insert(
            """INSERT INTO tasks (task_id, patient_id, task_type, title, priority,
               status, due_date, assigned_to, assigned_to_doctor)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (self.task_id, self.patient_id, self.task_type, self.title,
             self.priority if isinstance(self.priority, str) else self.priority.value,
             status_val, self.due_date, self.assigned_to, self.assigned_to_doctor),
        )
        log.info("Task.save | success | task_id=%s", self.task_id)

    @classmethod
    def get_by_id(cls, task_id: str) -> Optional["Task"]:
        row = execute_one("SELECT * FROM tasks WHERE task_id = %s", (task_id,))
        return cls.from_row(row) if row else None

    @classmethod
    def list_paginated(cls, status: str, cursor: str = None, limit: int = 20) -> Dict:
        base_query = "SELECT * FROM tasks WHERE status = %s"
        query, params = build_paginated_query(base_query, "created_at", cursor, limit)
        params = [status] + params
        rows = execute(query, tuple(params))
        items = [cls.from_row(r).to_dict() for r in rows]
        next_cursor = None
        if items:
            next_cursor = encode_cursor({"after": items[-1]["created_at"]})
        return {"items": items, "next_cursor": next_cursor}

    @classmethod
    def list_for_doctor(cls, doctor_id: str) -> List["Task"]:
        rows = execute(
            "SELECT * FROM tasks WHERE assigned_to_doctor = %s AND status = 'pending' ORDER BY due_date",
            (doctor_id,),
        )
        return [cls.from_row(r) for r in rows]
