"""Order handler — medication order lifecycle (stub)."""

import json
import logging
from typing import Dict, Any

from laso.enums import UserRole
from laso.utils.auth import extract_user, check_role
from laso.utils.response import success, created, error
from laso.exceptions import ValidationError, NotFoundError

log = logging.getLogger(__name__)

_WRITE_ROLES = (UserRole.COORDINATOR, UserRole.ADMIN)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = event.get("httpMethod", "")
    resource = event.get("resource", "")
    route = f"{method} {resource}"
    log.info("order_handler | route=%s", route)

    route_map = {
        "POST /orders": create,
        "GET /orders/patient/{patientId}": list_for_patient,
        "GET /orders/recent": list_recent,
        "PUT /orders/{id}/advance": advance,
    }

    handler = route_map.get(route)
    if not handler:
        return error(404, "Route not found", "NOT_FOUND")

    try:
        user = extract_user(event)
        if not user:
            return error(401, "Unauthorized", "UNAUTHORIZED")
        return handler(event, user)
    except ValidationError as e:
        return error(422, e.message, e.code, e.details)
    except NotFoundError as e:
        return error(404, e.message, e.code)
    except Exception:
        log.exception("order_handler | unhandled error")
        return error(500, "Internal server error", "INTERNAL_ERROR")


def create(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import order_service

    denied = check_role(user, *_WRITE_ROLES)
    if denied:
        return denied

    body = json.loads(event.get("body", "{}"))
    result = order_service.create(body=body)
    return created(result)


def list_for_patient(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import order_service

    patient_id = event["pathParameters"]["patientId"]
    result = order_service.list_for_patient(patient_id=patient_id)
    return success(result)


def list_recent(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import order_service

    result = order_service.list_recent()
    return success(result)


def advance(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import order_service

    denied = check_role(user, *_WRITE_ROLES)
    if denied:
        return denied

    order_id = event["pathParameters"]["id"]
    body = json.loads(event.get("body", "{}"))
    result = order_service.advance(order_id=order_id, body=body)
    return success(result)
