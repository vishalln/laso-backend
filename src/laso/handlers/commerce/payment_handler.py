"""Payment handler — initiation and status (stub)."""

import json
import logging
from typing import Dict, Any

from laso.utils.auth import extract_user
from laso.utils.response import success, created, error
from laso.utils.validation import validate_required
from laso.exceptions import ValidationError, NotFoundError

log = logging.getLogger(__name__)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = event.get("httpMethod", "")
    resource = event.get("resource", "")
    route = f"{method} {resource}"
    log.info("payment_handler | route=%s", route)

    route_map = {
        "POST /payments/initiate": initiate,
        "GET /payments/{id}/status": get_status,
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
        log.exception("payment_handler | unhandled error")
        return error(500, "Internal server error", "INTERNAL_ERROR")


def initiate(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import payment_service

    body = json.loads(event.get("body", "{}"))
    validate_required(body, ["programme_id", "amount"])

    result = payment_service.initiate(
        programme_id=body["programme_id"],
        patient_id=user.id,
        amount=body["amount"],
    )
    return created(result)


def get_status(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import payment_service

    payment_id = event["pathParameters"]["id"]
    result = payment_service.get_status(payment_id=payment_id)
    return success(result)
