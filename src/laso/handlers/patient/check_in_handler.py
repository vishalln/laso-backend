"""Check-in handler — patient check-in submissions and adherence tracking."""

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
    log.info("check_in_handler | route=%s", route)

    route_map = {
        "POST /check-ins": submit,
        "GET /check-ins/programme/{programmeId}": list_for_programme,
        "GET /check-ins/latest/{patientId}": get_latest,
        "GET /check-ins/adherence/{programmeId}": get_adherence,
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
        log.exception("check_in_handler | unhandled error")
        return error(500, "Internal server error", "INTERNAL_ERROR")


def submit(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import check_in_service

    body = json.loads(event.get("body", "{}"))
    result = check_in_service.submit(patient_id=user.id, programme_id=body.get("programme_id"), body=body)
    return created(result)


def list_for_programme(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import check_in_service

    programme_id = event["pathParameters"]["programmeId"]
    params = event.get("queryStringParameters") or {}
    limit = int(params["limit"]) if params.get("limit") else 20
    result = check_in_service.list_for_programme(
        programme_id=programme_id, cursor=params.get("next_token"), limit=limit
    )
    return paginated(result["items"], result.get("next_cursor"))


def get_latest(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import check_in_service

    patient_id = event["pathParameters"]["patientId"]
    result = check_in_service.get_latest(patient_id=patient_id)
    return success(result)


def get_adherence(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import check_in_service

    programme_id = event["pathParameters"]["programmeId"]
    result = check_in_service.get_adherence(programme_id=programme_id)
    return success(result)
