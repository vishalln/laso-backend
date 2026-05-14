"""Task service — creation, toggling, listing for coordinators and doctors."""

import logging
from datetime import date, timedelta
from uuid import uuid4

from laso.enums.task import TaskStatus, TaskPriority
from laso.exceptions import NotFoundError
from laso.models.task import Task
from laso.models.consultation import Consultation

log = logging.getLogger(__name__)

DEFAULT_DUE_DAYS = 3


def create_task(
    patient_id: str,
    task_type: str,
    title: str,
    priority: str,
    due_date=None,
    assigned_to: str = None,
    assigned_to_doctor: str = None,
) -> str:
    """Create a task and return task_id."""
    log.info("task_service.create_task | patient_id=%s type=%s", patient_id, task_type)

    task_id = str(uuid4())
    task = Task(
        task_id=task_id,
        patient_id=patient_id,
        task_type=task_type,
        title=title,
        priority=priority,
        status=TaskStatus.PENDING,
        due_date=due_date or (date.today() + timedelta(days=DEFAULT_DUE_DAYS)).isoformat(),
        assigned_to=assigned_to,
        assigned_to_doctor=assigned_to_doctor,
    )
    task.save()

    log.info("task_service.create_task | task_id=%s", task_id)
    return task_id


def toggle(task_id: str) -> dict:
    log.info("task_service.toggle | task_id=%s", task_id)

    task = Task.get_by_id(task_id)
    if not task:
        raise NotFoundError("Task not found")

    new_status = TaskStatus.DONE if task.status == TaskStatus.PENDING else TaskStatus.PENDING

    from laso.utils.db import update_by_id
    update_by_id("tasks", "task_id", task_id, status=new_status.value)

    task.status = new_status
    log.info("task_service.toggle | task_id=%s new_status=%s", task_id, new_status.value)
    return task.to_dict()


def list_for_coordinator(status: str, cursor: str = None, limit: int = 20) -> dict:
    """Paginated task list for coordinators."""
    log.info("task_service.list_for_coordinator | status=%s cursor=%s limit=%d", status, cursor, limit)
    result = Task.list_paginated(status=status, cursor=cursor, limit=limit)
    log.info("task_service.list_for_coordinator | count=%d", len(result.get("items", [])))
    return result


def list_for_doctor(doctor_id: str) -> list:
    """Compute pending actions for a doctor."""
    log.info("task_service.list_for_doctor | doctor_id=%s", doctor_id)
    tasks = Task.list_for_doctor(doctor_id)
    log.info("task_service.list_for_doctor | count=%d", len(tasks))
    return [t.to_dict() for t in tasks]
