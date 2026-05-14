"""Standardised API Gateway response builders with CORS headers."""

import json
import logging
from typing import Any, Optional

log = logging.getLogger(__name__)

_CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,PUT,POST,DELETE,OPTIONS",
}


def _response(status: int, body: dict) -> dict:
    return {"statusCode": status, "headers": _CORS_HEADERS, "body": json.dumps(body, default=str)}


def success(data: Any, status: int = 200) -> dict:
    log.info("response.success | status=%d", status)
    return _response(status, {"data": data})


def created(data: Any) -> dict:
    log.info("response.created | status=201")
    return _response(201, {"data": data})


def paginated(data: list, next_token: Optional[str], total: Optional[int] = None) -> dict:
    log.info("response.paginated | count=%d has_next=%s", len(data), bool(next_token))
    body: dict = {"data": data, "next_token": next_token}
    if total is not None:
        body["total"] = total
    return _response(200, body)


def error(status: int, message: str, code: str, details: Optional[Any] = None) -> dict:
    log.warning("response.error | status=%d code=%s message=%s", status, code, message)
    body: dict = {"error": {"message": message, "code": code}}
    if details:
        body["error"]["details"] = details
    return _response(status, body)
