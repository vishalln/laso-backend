"""Quiz handler — submission, results retrieval, claim."""

import json
import logging
from typing import Dict, Any

from laso.utils.auth import extract_user
from laso.utils.response import success, error
from laso.exceptions import ValidationError, NotFoundError, ForbiddenError, ConflictError

log = logging.getLogger(__name__)

_ANONYMOUS_ROUTES = frozenset({
    "POST /quiz/submit",
})


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = event.get("httpMethod", "")
    resource = event.get("resource", "")
    route = f"{method} {resource}"
    log.info("quiz_handler | route=%s", route)

    route_map = {
        "POST /quiz/submit": submit,
        "GET /quiz/result": get_result,
        "GET /quiz/patient/{patientId}": get_patient_quiz,
        "POST /quiz/claim/{quizId}": claim_quiz,
    }

    handler = route_map.get(route)
    if not handler:
        return error(404, "Route not found", "NOT_FOUND")

    try:
        user = extract_user(event)

        if route not in _ANONYMOUS_ROUTES and not user:
            return error(401, "Unauthorized", "UNAUTHORIZED")

        return handler(event, user)
    except ForbiddenError as e:
        return error(403, e.message, e.code)
    except ConflictError as e:
        return error(409, e.message, e.code)
    except ValidationError as e:
        return error(422, e.message, e.code, e.details)
    except NotFoundError as e:
        return error(404, e.message, e.code)
    except Exception:
        log.exception("quiz_handler | unhandled error")
        return error(500, "Internal server error", "INTERNAL_ERROR")


def submit(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import quiz_service

    body = json.loads(event.get("body", "{}"))
    patient_id = user.id if user else None
    result = quiz_service.submit(patient_id=patient_id, data=body)
    return success(result)


def get_result(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import quiz_service

    result = quiz_service.get_latest(patient_id=user.id)
    return success(result)


def get_patient_quiz(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import quiz_service

    patient_id = event["pathParameters"]["patientId"]
    result = quiz_service.get_latest(patient_id=patient_id)
    return success(result)


def claim_quiz(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import quiz_service

    quiz_id = event["pathParameters"]["quizId"]
    log.info("quiz_handler.claim_quiz | quiz_id=%s user_id=%s", quiz_id, user.id)
    result = quiz_service.claim(quiz_id=quiz_id, patient_id=user.id)
    return success(result)
