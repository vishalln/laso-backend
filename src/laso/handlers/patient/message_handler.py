"""Message handler — in-app messaging between patients and care team."""

import json
import logging
from typing import Dict, Any

from laso.enums import UserRole
from laso.utils.auth import extract_user, check_role
from laso.utils.response import success, created, paginated, error
from laso.exceptions import ValidationError, NotFoundError, ForbiddenError

log = logging.getLogger(__name__)

_STAFF_ROLES = (UserRole.DOCTOR, UserRole.COORDINATOR, UserRole.ADMIN)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = event.get("httpMethod", "")
    resource = event.get("resource", "")
    route = f"{method} {resource}"
    log.info("message_handler | route=%s", route)

    route_map = {
        "POST /messages": send,
        "GET /messages/{conversationId}": get_messages,
        "GET /messages/conversation/{patientId}": get_conversation_for_patient,
        "GET /messages/recent-sent": recent_sent,
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
        log.exception("message_handler | unhandled error")
        return error(500, "Internal server error", "INTERNAL_ERROR")


def send(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import message_service

    body = json.loads(event.get("body", "{}"))
    patient_id = body.get("patient_id") or (user.id if user.role == UserRole.PATIENT else None)

    result = message_service.send(
        patient_id=patient_id,
        sender_id=user.id,
        sender_role=user.role.value,
        sender_name=user.name,
        text=body.get("text") or body.get("body"),
    )
    return created(result)


def get_messages(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import message_service

    conversation_id = event["pathParameters"]["conversationId"]
    params = event.get("queryStringParameters") or {}
    limit = int(params["limit"]) if params.get("limit") else 50
    result = message_service.get_messages(
        conversation_id=conversation_id, after=params.get("after"), limit=limit
    )
    return paginated(result["items"], result.get("next_cursor"))


def get_conversation_for_patient(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import message_service

    patient_id = event["pathParameters"]["patientId"]
    result = message_service.get_conversation_for_patient(patient_id=patient_id)
    return success(result)


def recent_sent(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import message_service

    result = message_service.recent_sent(sender_id=user.id)
    return success(result)
