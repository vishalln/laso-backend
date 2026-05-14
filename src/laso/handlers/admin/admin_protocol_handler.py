"""Admin protocol template management handler."""

import json
import logging
from typing import Dict, Any

from laso.enums import UserRole
from laso.utils.auth import require_role
from laso.utils.response import success, created, error
from laso.exceptions import ValidationError, NotFoundError, ConflictError, ForbiddenError

log = logging.getLogger(__name__)


@require_role(UserRole.ADMIN)
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = event.get("httpMethod", "")
    resource = event.get("resource", "")
    route = f"{method} {resource}"
    log.info("admin_protocol_handler | route=%s", route)

    route_map = {
        "GET /admin/protocol/templates": list_templates,
        "GET /admin/protocol/templates/{id}": get_template,
        "GET /admin/protocol/templates/{id}/versions": list_versions,
        "GET /admin/protocol/templates/published": get_published,
        "POST /admin/protocol/templates/{id}/steps": add_step,
        "PUT /admin/protocol/templates/{id}/steps/{stepId}": update_step,
        "DELETE /admin/protocol/templates/{id}/steps/{stepId}": delete_step,
        "PUT /admin/protocol/templates/{id}/steps/reorder": reorder_steps,
        "POST /admin/protocol/templates/{id}/publish": publish,
    }

    handler = route_map.get(route)
    if not handler:
        return error(404, "Route not found", "NOT_FOUND")

    try:
        return handler(event)
    except ForbiddenError as e:
        return error(403, e.message, e.code)
    except ValidationError as e:
        return error(422, e.message, e.code, e.details)
    except NotFoundError as e:
        return error(404, e.message, e.code)
    except ConflictError as e:
        return error(409, e.message, e.code, e.details)
    except Exception:
        log.exception("admin_protocol_handler | unhandled error")
        return error(500, "Internal server error", "INTERNAL_ERROR")


def list_templates(event: Dict[str, Any]) -> Dict[str, Any]:
    from laso.utils.db import execute
    from laso.models.protocol import ProtocolTemplate

    rows = execute("SELECT * FROM protocol_templates ORDER BY created_at DESC")
    result = [ProtocolTemplate.from_row(r).to_dict() for r in rows]
    return success(result)


def get_template(event: Dict[str, Any]) -> Dict[str, Any]:
    from laso.services import admin_protocol_service

    template_id = event["pathParameters"]["id"]
    result = admin_protocol_service.get_template(template_id=template_id)
    return success(result)


def list_versions(event: Dict[str, Any]) -> Dict[str, Any]:
    from laso.services import admin_protocol_service

    template_id = event["pathParameters"]["id"]
    result = admin_protocol_service.list_versions(template_id=template_id)
    return success(result)


def get_published(event: Dict[str, Any]) -> Dict[str, Any]:
    from laso.services import admin_protocol_service

    result = admin_protocol_service.get_published()
    return success(result)


def add_step(event: Dict[str, Any]) -> Dict[str, Any]:
    from laso.services import admin_protocol_service

    template_id = event["pathParameters"]["id"]
    body = json.loads(event.get("body", "{}"))
    result = admin_protocol_service.add_step(template_id=template_id, body=body)
    return created(result)


def update_step(event: Dict[str, Any]) -> Dict[str, Any]:
    from laso.services import admin_protocol_service

    step_id = event["pathParameters"]["stepId"]
    body = json.loads(event.get("body", "{}"))
    result = admin_protocol_service.update_step(step_id=step_id, body=body)
    return success(result)


def delete_step(event: Dict[str, Any]) -> Dict[str, Any]:
    from laso.services import admin_protocol_service

    step_id = event["pathParameters"]["stepId"]
    result = admin_protocol_service.delete_step(step_id=step_id)
    return success(result)


def reorder_steps(event: Dict[str, Any]) -> Dict[str, Any]:
    from laso.services import admin_protocol_service

    template_id = event["pathParameters"]["id"]
    body = json.loads(event.get("body", "{}"))
    result = admin_protocol_service.reorder_steps(template_id=template_id, step_ids=body["step_ids"])
    return success(result)


def publish(event: Dict[str, Any]) -> Dict[str, Any]:
    from laso.services import admin_protocol_service

    template_id = event["pathParameters"]["id"]
    user = event["_user"]
    result = admin_protocol_service.publish(template_id=template_id, admin_email=user.email)
    return success(result)
