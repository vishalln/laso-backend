"""Dashboard handler — patient-facing dashboard computations."""

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
    log.info("dashboard_handler | route=%s", route)

    route_map = {
        "GET /dashboard/next-action": compute_next_action,
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
        log.exception("dashboard_handler | unhandled error")
        return error(500, "Internal server error", "INTERNAL_ERROR")


def compute_next_action(event: Dict[str, Any], user) -> Dict[str, Any]:
    from laso.services import dashboard_service, programme_service

    programme = programme_service.get_active(patient_id=user.id)
    result = dashboard_service.compute_next_action(patient_id=user.id, programme_id=programme["programme_id"])
    return success(result)
