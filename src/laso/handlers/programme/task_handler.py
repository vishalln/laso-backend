"""Task handler — coordinator and doctor task management."""

import logging
from typing import Dict, Any

from laso.utils.auth import extract_user
from laso.utils.response import success, error
from laso.exceptions import ValidationError, NotFoundError, ConflictError, ForbiddenError

log = logging.getLogger(__name__)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = event.get("httpMethod", "")
    resource = event.get("resource", "")
    route = f"{method} {resource}"
    log.info("task_handler | route=%s", route)

    route_map = {
        "GET /tasks": list_for_coordinator,
        "GET /tasks/doctor": list_for_doctor,
        "PUT /tasks/{id}/toggle": toggle,
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
        log.exception("task_handler | unhandled error")
        return error(500, "Internal server error", "INTERNAL_ERROR")


def list_for_coordinator(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import task_service

    params = event.get("queryStringParameters") or {}
    limit = int(params["limit"]) if params.get("limit") else 20
    result = task_service.list_for_coordinator(
        status=params.get("status", "pending"),
        cursor=params.get("cursor"),
        limit=limit,
    )
    return success(result)


def list_for_doctor(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import task_service

    result = task_service.list_for_doctor(doctor_id=user.id)
    return success(result)


def toggle(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import task_service

    task_id = event["pathParameters"]["id"]
    result = task_service.toggle(task_id=task_id)
    return success(result)
