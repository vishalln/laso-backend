"""Not found error."""

from typing import Any, Optional

from .base import LasoError


class NotFoundError(LasoError):
    code = "NOT_FOUND"

    def __init__(self, message: str = "Resource not found", details: Optional[Any] = None):
        super().__init__(message=message, details=details)
