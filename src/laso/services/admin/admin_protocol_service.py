"""Admin protocol template management service."""

import json
import logging
from datetime import datetime
from uuid import uuid4

from laso.exceptions import NotFoundError
from laso.models.protocol import ProtocolTemplate, ProtocolTemplateStep, ProtocolTemplateVersion
from laso.utils.db import execute, update_by_id, delete_by_id

log = logging.getLogger(__name__)


def get_template(template_id: str) -> dict:
    """Return template with steps."""
    log.info("admin_protocol_service.get_template | template_id=%s", template_id)
    template = ProtocolTemplate.get_by_id(template_id)
    if not template:
        raise NotFoundError("Template not found")
    steps = [s.to_dict() for s in ProtocolTemplateStep.list_for_template(template_id)]
    return {**template.to_dict(), "steps": steps}


def get_published() -> dict:
    """Return latest published template with steps."""
    log.info("admin_protocol_service.get_published")
    template = ProtocolTemplate.get_published()
    if not template:
        raise NotFoundError("No published template found")
    steps = [s.to_dict() for s in ProtocolTemplateStep.list_for_template(template.template_id)]
    return {**template.to_dict(), "steps": steps}


def add_step(template_id: str, body: dict) -> dict:
    """Add a step to a template."""
    log.info("admin_protocol_service.add_step | template_id=%s", template_id)
    from laso.enums import StepType, AutoActivateRule

    existing = ProtocolTemplateStep.list_for_template(template_id)
    sort_order = len(existing)

    step = ProtocolTemplateStep(
        step_id=str(uuid4()),
        template_id=template_id,
        title=body["title"],
        step_type=StepType(body["step_type"]),
        week_offset=body.get("week_offset", 0),
        duration_minutes=body.get("duration_minutes", 0),
        is_recurring=body.get("is_recurring", False),
        auto_activate_rule=AutoActivateRule(body.get("auto_activate_rule", "manual")),
        is_flagged=body.get("is_flagged", False),
        sort_order=sort_order,
    )
    step.save()
    return step.to_dict()


def update_step(step_id: str, body: dict) -> dict:
    """Update a template step."""
    log.info("admin_protocol_service.update_step | step_id=%s", step_id)
    allowed = {"title", "step_type", "week_offset", "duration_minutes",
               "is_recurring", "auto_activate_rule", "is_flagged"}
    fields = {k: v for k, v in body.items() if k in allowed}
    update_by_id("protocol_template_steps", "step_id", step_id, **fields)
    row = execute("SELECT * FROM protocol_template_steps WHERE step_id = %s", (step_id,))
    return ProtocolTemplateStep.from_row(row[0]).to_dict() if row else {}


def delete_step(step_id: str) -> dict:
    """Delete a template step."""
    log.info("admin_protocol_service.delete_step | step_id=%s", step_id)
    delete_by_id("protocol_template_steps", "step_id", step_id)
    return {"deleted": True, "step_id": step_id}


def reorder_steps(template_id: str, step_ids: list) -> dict:
    """Reorder steps by updating sort_order."""
    log.info("admin_protocol_service.reorder_steps | template_id=%s", template_id)
    for idx, sid in enumerate(step_ids):
        update_by_id("protocol_template_steps", "step_id", sid, sort_order=idx)
    steps = [s.to_dict() for s in ProtocolTemplateStep.list_for_template(template_id)]
    return {"steps": steps}


def publish(template_id: str, admin_email: str) -> dict:
    """Publish template: increment version, snapshot steps, set status."""
    log.info("admin_protocol_service.publish | template_id=%s", template_id)
    template = ProtocolTemplate.get_by_id(template_id)
    if not template:
        raise NotFoundError("Template not found")

    new_version = template.version + 1
    steps = [s.to_dict() for s in ProtocolTemplateStep.list_for_template(template_id)]

    version_record = ProtocolTemplateVersion(
        id=str(uuid4()),
        template_id=template_id,
        version=new_version,
        published_at=datetime.utcnow(),
        published_by=admin_email,
        step_count=len(steps),
        steps_snapshot=steps,
    )
    version_record.save()

    update_by_id("protocol_templates", "template_id", template_id,
                 version=new_version, status="published",
                 published_at=datetime.utcnow(), published_by=admin_email)

    return {**get_template(template_id), "version": new_version}


def list_versions(template_id: str) -> list:
    """List all published versions."""
    log.info("admin_protocol_service.list_versions | template_id=%s", template_id)
    return [v.to_dict() for v in ProtocolTemplateVersion.list_for_template(template_id)]
