"""Master router — dispatches API Gateway proxy events to domain handlers.

Uses route config from laso.constants.routes as single source of truth.
Reconstructs the API Gateway `resource` field from the actual request path
so domain handlers can match their internal route maps.
"""

import re
import logging
import importlib
from typing import Callable, Optional

from laso.constants.routes import DOMAIN_HANDLERS, ADMIN_SUB_HANDLERS, RESOURCE_PATTERNS

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Cache: module_path → lambda_handler function
_handler_cache: dict[str, Callable] = {}

# Compiled resource patterns for path → resource matching
_compiled_patterns: list[tuple[re.Pattern, str]] = []


def _compile_patterns():
    """Compile RESOURCE_PATTERNS into regex for matching actual paths."""
    if _compiled_patterns:
        return
    for pattern in RESOURCE_PATTERNS:
        # Convert {param} to regex group that matches any non-slash segment
        regex_str = re.sub(r"\{[^}]+\}", r"[^/]+", pattern)
        regex_str = f"^{regex_str}$"
        _compiled_patterns.append((re.compile(regex_str), pattern))
    # Sort by specificity (more segments first, then static over dynamic)
    _compiled_patterns.sort(key=lambda x: (-x[1].count("/"), x[1].count("{")))


def _resolve_resource(path: str) -> str:
    """Match an actual path to its resource pattern (with {param} placeholders)."""
    _compile_patterns()
    for regex, pattern in _compiled_patterns:
        if regex.match(path):
            return pattern
    return path


def _load_handler(module_path: str) -> Callable:
    """Import and cache a handler's lambda_handler function."""
    if module_path not in _handler_cache:
        module = importlib.import_module(module_path)
        _handler_cache[module_path] = module.lambda_handler
    return _handler_cache[module_path]


def _get_handler_for_path(parts: list[str]) -> Optional[Callable]:
    """Determine which domain handler should process this request."""
    if not parts:
        return None

    prefix = parts[0]

    # Admin routes: /admin/{sub}/...
    if prefix == "admin" and len(parts) >= 2:
        sub = parts[1]
        module_path = ADMIN_SUB_HANDLERS.get(sub)
        if module_path:
            return _load_handler(module_path)
        return None

    # Standard domain routes
    module_path = DOMAIN_HANDLERS.get(prefix)
    if module_path:
        return _load_handler(module_path)

    return None


_CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,PUT,POST,DELETE,OPTIONS",
}


def lambda_handler(event, context):
    """Route proxy integration events to the correct domain handler."""
    path = event.get("path", "")
    method = event.get("httpMethod", "")
    log.info("router | method=%s path=%s", method, path)

    if method == "OPTIONS":
        return {"statusCode": 200, "headers": _CORS_HEADERS, "body": ""}

    parts = [p for p in path.split("/") if p]
    handler = _get_handler_for_path(parts)

    if not handler:
        log.warning("router | no_handler path=%s", path)
        return {
            "statusCode": 404,
            "headers": {"Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"},
            "body": '{"error":"Route not found","code":"NOT_FOUND"}',
        }

    # Reconstruct the `resource` field so domain handlers can match routes
    resource = _resolve_resource(path)
    event["resource"] = resource

    # Extract path parameters from the actual path vs the pattern
    path_params = {}
    resource_parts = resource.split("/")
    path_parts = path.split("/")
    for rp, pp in zip(resource_parts, path_parts):
        if rp.startswith("{") and rp.endswith("}"):
            param_name = rp[1:-1]
            path_params[param_name] = pp
    event["pathParameters"] = path_params or event.get("pathParameters")

    return handler(event, context)
