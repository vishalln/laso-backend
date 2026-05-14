"""Patient handler — profile, flags, doctor panel."""

import json
import logging
from typing import Dict, Any

from laso.enums import UserRole
from laso.utils.auth import extract_user, check_role
from laso.utils.response import success, created, error
from laso.exceptions import ValidationError, NotFoundError, ForbiddenError

log = logging.getLogger(__name__)

_STAFF_ROLES = (UserRole.DOCTOR, UserRole.COORDINATOR, UserRole.ADMIN)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = event.get("httpMethod", "")
    resource = event.get("resource", "")
    route = f"{method} {resource}"
    log.info("patient_handler | route=%s", route)

    route_map = {
        "GET /patients/me": get_me,
        "PUT /patients/me/profile": update_profile,
        "GET /patients/{id}": get_by_id,
        "GET /patients/{id}/flags": get_flags,
        "POST /patients/{id}/flags": set_flag,
        "DELETE /patients/{id}/flags/{flagId}": clear_flag,
        "GET /patients/doctor/{doctorId}": list_for_doctor,
        "GET /patients/doctor/{doctorId}/summary": get_summary,
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
    except Exception:
        log.exception("patient_handler | unhandled error")
        return error(500, "Internal server error", "INTERNAL_ERROR")


def get_me(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import patient_service

    result = patient_service.get_by_id(patient_id=user.id)
    return success(result)


def update_profile(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import patient_service

    body = json.loads(event.get("body", "{}"))
    result = patient_service.update_profile(patient_id=user.id, data=body)
    return success(result)


def get_by_id(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import patient_service

    denied = check_role(user, *_STAFF_ROLES)
    if denied:
        return denied

    patient_id = event["pathParameters"]["id"]
    result = patient_service.get_by_id(patient_id=patient_id)
    return success(result)


def get_flags(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import patient_service

    denied = check_role(user, *_STAFF_ROLES)
    if denied:
        return denied

    patient_id = event["pathParameters"]["id"]
    result = patient_service.get_flags(patient_id=patient_id)
    return success(result)


def set_flag(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import patient_service

    denied = check_role(user, *_STAFF_ROLES)
    if denied:
        return denied

    patient_id = event["pathParameters"]["id"]
    body = json.loads(event.get("body", "{}"))
    result = patient_service.set_flag(patient_id=patient_id, data=body, user=user)
    return created(result)


def clear_flag(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import patient_service

    denied = check_role(user, *_STAFF_ROLES)
    if denied:
        return denied

    patient_id = event["pathParameters"]["id"]
    flag_id = event["pathParameters"]["flagId"]
    result = patient_service.clear_flag(patient_id=patient_id, flag_id=flag_id, user=user)
    return success(result)


def list_for_doctor(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import patient_service

    denied = check_role(user, *_STAFF_ROLES)
    if denied:
        return denied

    doctor_id = event["pathParameters"]["doctorId"]
    result = patient_service.list_for_doctor(doctor_id=doctor_id)
    return success(result)


def get_summary(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import patient_service

    denied = check_role(user, *_STAFF_ROLES)
    if denied:
        return denied

    doctor_id = event["pathParameters"]["doctorId"]
    patients = patient_service.list_for_doctor(doctor_id=doctor_id)
    flags = patient_service.get_flags(doctor_id) if patients else []

    result = {
        "total_patients": len(patients),
        "flagged_patients": len(flags),
    }
    return success(result)
