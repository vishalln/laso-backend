"""Conflict error."""

from typing import Any, Optional

from .base import LasoError


class ConflictError(LasoError):
    code = "CONFLICT"

    def __init__(self, message: str = "Resource conflict", details: Optional[Any] = None):
        super().__init__(message=message, details=details)
