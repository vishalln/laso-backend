"""Admin doctor management handler."""

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
    log.info("admin_doctor_handler | route=%s", route)

    route_map = {
        "GET /admin/doctors": list_all,
        "POST /admin/doctors": create,
        "PUT /admin/doctors/{id}": update,
        "PUT /admin/doctors/{id}/status": toggle_status,
        "DELETE /admin/doctors/{id}": delete,
        "GET /admin/doctors/{id}/availability": get_availability,
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
        log.exception("admin_doctor_handler | unhandled error")
        return error(500, "Internal server error", "INTERNAL_ERROR")


def list_all(event: Dict[str, Any]) -> Dict[str, Any]:
    from laso.services import admin_doctor_service

    result = admin_doctor_service.list_all()
    return success(result)


def create(event: Dict[str, Any]) -> Dict[str, Any]:
    from laso.services import admin_doctor_service

    body = json.loads(event.get("body", "{}"))
    result = admin_doctor_service.create(body=body)
    return created(result)


def update(event: Dict[str, Any]) -> Dict[str, Any]:
    from laso.services import admin_doctor_service

    doctor_id = event["pathParameters"]["id"]
    body = json.loads(event.get("body", "{}"))
    result = admin_doctor_service.update(doctor_id=doctor_id, body=body)
    return success(result)


def toggle_status(event: Dict[str, Any]) -> Dict[str, Any]:
    from laso.services import admin_doctor_service

    doctor_id = event["pathParameters"]["id"]
    body = json.loads(event.get("body", "{}"))
    result = admin_doctor_service.toggle_status(doctor_id=doctor_id, status=body["status"])
    return success(result)


def delete(event: Dict[str, Any]) -> Dict[str, Any]:
    from laso.services import admin_doctor_service

    doctor_id = event["pathParameters"]["id"]
    result = admin_doctor_service.delete(doctor_id=doctor_id)
    return success(result)


def get_availability(event: Dict[str, Any]) -> Dict[str, Any]:
    from laso.services import admin_doctor_service

    doctor_id = event["pathParameters"]["id"]
    result = admin_doctor_service.get_availability(doctor_id=doctor_id)
    return success(result)
