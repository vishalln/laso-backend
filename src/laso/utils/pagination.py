"""Cursor-based pagination utilities."""

import base64
import json
import logging
from typing import Optional

from laso.constants.config import PAGINATION_DEFAULT_LIMIT, PAGINATION_MAX_LIMIT

log = logging.getLogger(__name__)


def encode_cursor(data: dict) -> str:
    """Encode cursor data to base64 JSON string."""
    return base64.urlsafe_b64encode(json.dumps(data).encode()).decode()


def decode_cursor(token: str) -> dict:
    """Decode base64 JSON cursor string to dict."""
    try:
        return json.loads(base64.urlsafe_b64decode(token.encode()).decode())
    except Exception as exc:
        log.warning("decode_cursor | invalid token error=%s", str(exc))
        return {}


def build_paginated_query(
    base_query: str,
    sort_col: str,
    cursor: Optional[str],
    limit: Optional[int] = None,
) -> tuple[str, list]:
    """Append cursor-based WHERE clause and LIMIT to a base query. Returns (query, params)."""
    params: list = []
    clauses = []

    if cursor:
        cursor_data = decode_cursor(cursor)
        if cursor_data.get("after"):
            clauses.append(f"{sort_col} > %s")
            params.append(cursor_data["after"])

    effective_limit = min(limit or PAGINATION_DEFAULT_LIMIT, PAGINATION_MAX_LIMIT)

    where = f" AND {' AND '.join(clauses)}" if clauses else ""
    query = f"{base_query}{where} ORDER BY {sort_col} ASC LIMIT %s"
    params.append(effective_limit)

    log.info("build_paginated_query | limit=%d has_cursor=%s", effective_limit, bool(cursor))
    return query, params
