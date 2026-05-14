"""Blood test handler — lab results and test management."""

import json
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
    log.info("blood_test_handler | route=%s", route)

    route_map = {
        "GET /blood-tests/{id}": get_by_id,
        "GET /blood-tests/programme/{programmeId}": list_for_programme,
        "PUT /blood-tests/{id}/results": enter_results,
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
        log.exception("blood_test_handler | unhandled error")
        return error(500, "Internal server error", "INTERNAL_ERROR")


def get_by_id(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import blood_test_service

    test_id = event["pathParameters"]["id"]
    result = blood_test_service.get_by_id(blood_test_id=test_id)
    return success(result)


def list_for_programme(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import blood_test_service

    programme_id = event["pathParameters"]["programmeId"]
    result = blood_test_service.list_for_programme(programme_id=programme_id)
    return success(result)


def enter_results(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import blood_test_service

    test_id = event["pathParameters"]["id"]
    body = json.loads(event.get("body", "{}"))
    result = blood_test_service.enter_results(blood_test_id=test_id, results=body, entered_by=user.id)
    return success(result)
