"""Admin analytics handler."""

import logging
from typing import Dict, Any

from laso.enums import UserRole
from laso.utils.auth import require_role
from laso.utils.response import success, error

log = logging.getLogger(__name__)


@require_role(UserRole.ADMIN, UserRole.COORDINATOR)
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = event.get("httpMethod", "")
    resource = event.get("resource", "")
    route = f"{method} {resource}"
    log.info("admin_analytics_handler | route=%s", route)

    route_map = {
        "GET /admin/analytics/overview": overview,
        "GET /admin/analytics/enrolment": enrolment,
        "GET /admin/analytics/weight-by-week": weight_by_week,
        "GET /admin/analytics/adherence-trend": adherence_trend,
        "GET /admin/analytics/status-distribution": status_distribution,
        "GET /admin/analytics/glucose-trend": glucose_trend,
        "GET /admin/analytics/side-effects": side_effects,
    }

    handler = route_map.get(route)
    if not handler:
        return error(404, "Route not found", "NOT_FOUND")

    try:
        return handler(event)
    except Exception:
        log.exception("admin_analytics_handler | unhandled error")
        return error(500, "Internal server error", "INTERNAL_ERROR")


def overview(event: Dict[str, Any]) -> Dict[str, Any]:
    from laso.services import analytics_service

    return success(analytics_service.overview())


def enrolment(event: Dict[str, Any]) -> Dict[str, Any]:
    from laso.services import analytics_service

    return success(analytics_service.enrolment_trend())


def weight_by_week(event: Dict[str, Any]) -> Dict[str, Any]:
    from laso.services import analytics_service

    return success(analytics_service.weight_by_week())


def adherence_trend(event: Dict[str, Any]) -> Dict[str, Any]:
    from laso.services import analytics_service

    return success(analytics_service.adherence_trend())


def status_distribution(event: Dict[str, Any]) -> Dict[str, Any]:
    from laso.services import analytics_service

    return success(analytics_service.status_distribution())


def glucose_trend(event: Dict[str, Any]) -> Dict[str, Any]:
    from laso.services import analytics_service

    return success(analytics_service.glucose_trend())


def side_effects(event: Dict[str, Any]) -> Dict[str, Any]:
    from laso.services import analytics_service

    return success(analytics_service.side_effects_top())
