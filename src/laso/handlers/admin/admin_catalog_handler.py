"""Catalog handler — public medication list + admin CRUD."""

import json
import logging
from typing import Dict, Any

from laso.enums import UserRole
from laso.utils.auth import extract_user, check_role
from laso.utils.response import success, created, error
from laso.exceptions import ValidationError, NotFoundError, ConflictError, ForbiddenError

log = logging.getLogger(__name__)

_PUBLIC_ROUTES = {"GET /catalog/medications"}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = event.get("httpMethod", "")
    resource = event.get("resource", "")
    route = f"{method} {resource}"
    log.info("admin_catalog_handler | route=%s", route)

    route_map = {
        "GET /catalog/medications": list_medications,
        "GET /admin/catalog": list_all,
        "POST /admin/catalog": create,
        "PUT /admin/catalog/{id}": update,
        "DELETE /admin/catalog/{id}": delete,
        "PUT /admin/catalog/{id}/stock": toggle_stock,
    }

    handler = route_map.get(route)
    if not handler:
        return error(404, "Route not found", "NOT_FOUND")

    try:
        user = extract_user(event)
        if not user:
            return error(401, "Unauthorized", "UNAUTHORIZED")

        if route not in _PUBLIC_ROUTES:
            denied = check_role(user, UserRole.ADMIN)
            if denied:
                return denied

        return handler(event)
    except ForbiddenError as e:
        return error(403, e.message, e.code)
    except ValidationError as e:
        return error(422, e.message, e.code, e.details)
    except NotFoundError as e:
        return error(404, e.message, e.code)
    except ConflictError as e:
        return error(409, e.message, e.code, e.details)
    except Exception:
        log.exception("admin_catalog_handler | unhandled error")
        return error(500, "Internal server error", "INTERNAL_ERROR")


def list_medications(event: Dict[str, Any]) -> Dict[str, Any]:
    from laso.services import admin_catalog_service

    result = admin_catalog_service.list_medications()
    return success(result)


def list_all(event: Dict[str, Any]) -> Dict[str, Any]:
    from laso.services import admin_catalog_service

    result = admin_catalog_service.list_all()
    return success(result)


def create(event: Dict[str, Any]) -> Dict[str, Any]:
    from laso.services import admin_catalog_service

    body = json.loads(event.get("body", "{}"))
    result = admin_catalog_service.create(body=body)
    return created(result)


def update(event: Dict[str, Any]) -> Dict[str, Any]:
    from laso.services import admin_catalog_service

    product_id = event["pathParameters"]["id"]
    body = json.loads(event.get("body", "{}"))
    result = admin_catalog_service.update(product_id=product_id, body=body)
    return success(result)


def delete(event: Dict[str, Any]) -> Dict[str, Any]:
    from laso.services import admin_catalog_service

    product_id = event["pathParameters"]["id"]
    result = admin_catalog_service.delete(product_id=product_id)
    return success(result)


def toggle_stock(event: Dict[str, Any]) -> Dict[str, Any]:
    from laso.services import admin_catalog_service

    product_id = event["pathParameters"]["id"]
    result = admin_catalog_service.toggle_stock(product_id=product_id)
    return success(result)
