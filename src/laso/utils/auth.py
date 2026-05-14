"""Auth utilities — token extraction and role-based access decorator."""

import functools
import logging
import os
from typing import Callable

from laso.enums import UserRole
from laso.constants.auth import ENV, AUTH_ERRORS
from laso.utils.cognito import CognitoClient
from laso.utils.response import error
from laso.models.auth import User

log = logging.getLogger(__name__)


def extract_user(event: dict) -> User | None:
    """Extract authenticated User from Bearer token via Cognito."""
    log.info("extract_user | extracting token")
    headers = event.get("headers") or {}
    auth_header = headers.get("Authorization") or headers.get("authorization") or ""
    if not auth_header.startswith("Bearer "):
        log.warning("extract_user | no bearer token")
        return None

    token = auth_header[7:]
    try:
        client = CognitoClient(
            user_pool_id=os.environ[ENV.USER_POOL_ID],
            client_id=os.environ[ENV.APP_CLIENT_ID],
        )
        cognito_data = client.get_user(token)
        email = next(
            (a["Value"] for a in cognito_data.get("UserAttributes", []) if a["Name"] == "email"),
            "",
        )
        groups = client.get_user_groups(email)
        user = User.from_cognito(cognito_data, groups)
        log.info("extract_user | success | user_id=%s role=%s", user.id, user.role.value)
        return user
    except Exception as exc:
        log.error("extract_user | failed | error=%s", str(exc))
        return None


def require_role(*roles: UserRole) -> Callable:
    """Decorator that checks user role before calling the handler."""

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(event, context=None):
            user = extract_user(event)
            if not user:
                return error(401, AUTH_ERRORS.ERROR_NO_TOKEN, "UNAUTHORIZED")
            if user.role not in roles:
                allowed = ", ".join(r.value for r in roles)
                log.warning("require_role | denied | user_role=%s allowed=%s", user.role.value, allowed)
                return error(403, AUTH_ERRORS.ERROR_ADMIN_ONLY, "FORBIDDEN")
            event["_user"] = user
            return fn(event, context)
        return wrapper
    return decorator


def check_role(user, *roles: UserRole) -> dict | None:
    """Inline role guard — returns error response if denied, None if allowed."""
    if user.role not in roles:
        allowed = ", ".join(r.value for r in roles)
        log.warning("check_role | denied | user_role=%s allowed=%s", user.role.value, allowed)
        return error(403, AUTH_ERRORS.ERROR_ADMIN_ONLY, "FORBIDDEN")
    return None
