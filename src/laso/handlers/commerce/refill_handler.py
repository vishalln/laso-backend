"""Refill handler — medication refill requests."""

import json
import logging
from typing import Dict, Any

from laso.utils.auth import extract_user
from laso.utils.response import created, error
from laso.exceptions import ValidationError, NotFoundError, ConflictError, ForbiddenError

log = logging.getLogger(__name__)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = event.get("httpMethod", "")
    resource = event.get("resource", "")
    route = f"{method} {resource}"
    log.info("refill_handler | route=%s", route)

    route_map = {
        "POST /refill-requests": request_refill,
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
        log.exception("refill_handler | unhandled error")
        return error(500, "Internal server error", "INTERNAL_ERROR")


def request_refill(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import refill_service

    body = json.loads(event.get("body", "{}"))
    result = refill_service.request_refill(patient_id=user.id, programme_id=body.get("programme_id"))
    return created(result)
