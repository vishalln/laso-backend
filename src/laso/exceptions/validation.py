"""Validation error."""

from typing import Any, Optional

from .base import LasoError


class ValidationError(LasoError):
    code = "VALIDATION_ERROR"

    def __init__(self, message: str = "Validation failed", details: Optional[Any] = None):
        super().__init__(message=message, details=details)
