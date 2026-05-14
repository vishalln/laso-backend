"""Treatment plan handler."""

import json
import logging
from typing import Dict, Any

from laso.utils.auth import extract_user
from laso.utils.response import success, error
from laso.exceptions import ValidationError, NotFoundError

log = logging.getLogger(__name__)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = event.get("httpMethod", "")
    resource = event.get("resource", "")
    route = f"{method} {resource}"
    log.info("treatment_plan_handler | route=%s", route)

    route_map = {
        "GET /treatment-plans/programme/{programmeId}": get,
        "PUT /treatment-plans/programme/{programmeId}": update,
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
        log.exception("treatment_plan_handler | unhandled error")
        return error(500, "Internal server error", "INTERNAL_ERROR")


def get(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import treatment_plan_service

    programme_id = event["pathParameters"]["programmeId"]
    result = treatment_plan_service.get_or_create(
        programme_id=programme_id, patient_id=user.id, doctor_id=user.id
    )
    return success(result)


def update(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import treatment_plan_service

    programme_id = event["pathParameters"]["programmeId"]
    body = json.loads(event.get("body", "{}"))
    result = treatment_plan_service.update(programme_id=programme_id, body=body)
    return success(result)
