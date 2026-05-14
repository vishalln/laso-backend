"""Prescription handler — medication prescriptions management."""

import json
import logging
from typing import Dict, Any

from laso.utils.auth import extract_user
from laso.utils.response import success, created, error
from laso.exceptions import ValidationError, NotFoundError, ConflictError, ForbiddenError

log = logging.getLogger(__name__)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = event.get("httpMethod", "")
    resource = event.get("resource", "")
    route = f"{method} {resource}"
    log.info("prescription_handler | route=%s", route)

    route_map = {
        "POST /prescriptions": create,
        "GET /prescriptions/patient/{patientId}": list_for_patient,
        "GET /prescriptions/active/{patientId}": get_active,
        "PUT /prescriptions/{id}/cancel": cancel,
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
        log.exception("prescription_handler | unhandled error")
        return error(500, "Internal server error", "INTERNAL_ERROR")


def create(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import prescription_service

    body = json.loads(event.get("body", "{}"))
    result = prescription_service.create(body=body, doctor_id=user.id)
    return created(result)


def list_for_patient(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import prescription_service

    patient_id = event["pathParameters"]["patientId"]
    result = prescription_service.list_for_patient(patient_id=patient_id)
    return success(result)


def get_active(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import prescription_service

    patient_id = event["pathParameters"]["patientId"]
    result = prescription_service.get_active(patient_id=patient_id)
    return success(result)


def cancel(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import prescription_service

    prescription_id = event["pathParameters"]["id"]
    body = json.loads(event.get("body", "{}"))
    result = prescription_service.cancel(
        prescription_id=prescription_id, reason=body.get("reason")
    )
    return success(result)
