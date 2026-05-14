"""Programme handler — programme lifecycle and step management."""

import json
import logging
from typing import Dict, Any

from laso.utils.auth import extract_user
from laso.utils.response import success, created, paginated, error
from laso.exceptions import ValidationError, NotFoundError, ConflictError, ForbiddenError

log = logging.getLogger(__name__)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = event.get("httpMethod", "")
    resource = event.get("resource", "")
    route = f"{method} {resource}"
    log.info("programme_handler | route=%s", route)

    route_map = {
        "POST /programmes": create,
        "GET /programmes/active": get_active,
        "GET /programmes/{id}": get_by_id,
        "GET /programmes/{id}/steps": get_steps,
        "GET /programmes/history": get_history,
        "PUT /programmes/{id}/status": update_status,
        "POST /programmes/{id}/steps": add_step,
        "PUT /programmes/{id}/steps/{stepId}/status": update_step_status,
    }

    handler = route_map.get(route)
    if not handler:
        return error(404, "Route not found", "NOT_FOUND")

    try:
        user = extract_user(event)
        if not user:
            return error(401, "Unauthorized", "UNAUTHORIZED")
        return handler(event, user)
    except ForbiddenError as e:
        return error(403, e.message, e.code)
    except ValidationError as e:
        return error(422, e.message, e.code, e.details)
    except NotFoundError as e:
        return error(404, e.message, e.code)
    except ConflictError as e:
        return error(409, e.message, e.code, e.details)
    except Exception:
        log.exception("programme_handler | unhandled error")
        return error(500, "Internal server error", "INTERNAL_ERROR")


def create(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import programme_service

    body = json.loads(event.get("body", "{}"))
    result = programme_service.create(patient_id=user.id, template_id=body.get("template_id"))
    return created(result)


def get_active(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import programme_service

    result = programme_service.get_active(patient_id=user.id)
    return success(result)


def get_by_id(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import programme_service

    programme_id = event["pathParameters"]["id"]
    result = programme_service.get_by_id(programme_id=programme_id)
    return success(result)


def get_steps(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import programme_service

    programme_id = event["pathParameters"]["id"]
    result = programme_service.get_steps(programme_id=programme_id)
    return success(result)


def get_history(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import programme_service

    result = programme_service.get_history(patient_id=user.id)
    return success(result)


def update_status(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import programme_service

    programme_id = event["pathParameters"]["id"]
    body = json.loads(event.get("body", "{}"))
    result = programme_service.update_status(
        programme_id=programme_id, status=body.get("status"), reason=body.get("reason")
    )
    return success(result)


def add_step(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import programme_service

    programme_id = event["pathParameters"]["id"]
    body = json.loads(event.get("body", "{}"))
    result = programme_service.add_step(programme_id=programme_id, body=body)
    return created(result)


def update_step_status(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import programme_service

    programme_id = event["pathParameters"]["id"]
    step_id = event["pathParameters"]["stepId"]
    body = json.loads(event.get("body", "{}"))
    status = body.get("status")

    if status == "completed":
        result = programme_service.complete_step(programme_id=programme_id, step_id=step_id)
    elif status == "skipped":
        result = programme_service.skip_step(
            programme_id=programme_id, step_id=step_id, reason=body.get("skip_reason", "")
        )
    else:
        return error(422, "Invalid step status", "INVALID_STATUS")

    return success(result)
