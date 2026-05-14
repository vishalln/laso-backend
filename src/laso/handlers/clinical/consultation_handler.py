"""Consultation handler — scheduling, context, and status management."""

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
    log.info("consultation_handler | route=%s", route)

    route_map = {
        "GET /consultations/{id}": get_by_id,
        "GET /consultations/{id}/context": get_context,
        "GET /consultations/patient/{patientId}": list_for_patient,
        "GET /consultations/doctor/{doctorId}": list_for_doctor,
        "GET /consultations/today": get_today,
        "GET /consultations/upcoming": get_upcoming,
        "POST /consultations/{id}/schedule": schedule,
        "PUT /consultations/{id}/meet-link": add_meet_link,
        "PUT /consultations/{id}/status": update_status,
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
        log.exception("consultation_handler | unhandled error")
        return error(500, "Internal server error", "INTERNAL_ERROR")


def get_by_id(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import consultation_service

    consultation_id = event["pathParameters"]["id"]
    result = consultation_service.get_by_id(consultation_id=consultation_id)
    return success(result)


def get_context(event: Dict[str, Any], user) -> Dict[str, Any]:
    """Aggregated patient context for doctor — calls multiple services."""
    from laso.services import (
        consultation_service,
        programme_service,
        blood_test_service,
        prescription_service,
        quiz_service,
    )

    consultation_id = event["pathParameters"]["id"]
    consultation = consultation_service.get_by_id(consultation_id=consultation_id)
    patient_id = consultation["patient_id"]

    programme = programme_service.get_active(patient_id=patient_id)
    programme_id = programme["programme_id"] if programme else None

    context_data = {
        "consultation": consultation,
        "programme": programme,
        "blood_tests": blood_test_service.list_for_programme(programme_id=programme_id) if programme_id else [],
        "prescriptions": prescription_service.list_for_patient(patient_id=patient_id),
        "quiz": quiz_service.get_latest(patient_id=patient_id),
        "past_consultations": consultation_service.list_for_patient(patient_id=patient_id),
    }
    return success(context_data)


def list_for_patient(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import consultation_service

    patient_id = event["pathParameters"]["patientId"]
    result = consultation_service.list_for_patient(patient_id=patient_id)
    return success(result)


def list_for_doctor(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import consultation_service

    doctor_id = event["pathParameters"]["doctorId"]
    result = consultation_service.list_for_doctor(doctor_id=doctor_id)
    return success(result)


def get_today(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import consultation_service

    result = consultation_service.get_today(doctor_id=user.id)
    return success(result)


def get_upcoming(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.enums import UserRole
    from laso.services import consultation_service

    if user.role == UserRole.PATIENT:
        result = consultation_service.get_upcoming_for_patient(patient_id=user.id)
    else:
        result = consultation_service.get_upcoming(doctor_id=user.id)
    return success(result)


def schedule(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import consultation_service

    consultation_id = event["pathParameters"]["id"]
    body = json.loads(event.get("body", "{}"))
    result = consultation_service.schedule(
        consultation_id=consultation_id,
        doctor_id=body.get("doctor_id"),
        scheduled_at=body.get("scheduled_at"),
    )
    return success(result)


def add_meet_link(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import consultation_service

    consultation_id = event["pathParameters"]["id"]
    body = json.loads(event.get("body", "{}"))
    result = consultation_service.add_meet_link(
        consultation_id=consultation_id, link=body.get("meet_link")
    )
    return success(result)


def update_status(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import consultation_service

    consultation_id = event["pathParameters"]["id"]
    body = json.loads(event.get("body", "{}"))
    result = consultation_service.update_status(
        consultation_id=consultation_id,
        status=body.get("status"),
        reason=body.get("cancel_reason"),
    )
    return success(result)
