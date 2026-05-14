"""Forbidden error."""

from typing import Any, Optional

from .base import LasoError


class ForbiddenError(LasoError):
    code = "FORBIDDEN"

    def __init__(self, message: str = "Access forbidden", details: Optional[Any] = None):
        super().__init__(message=message, details=details)
