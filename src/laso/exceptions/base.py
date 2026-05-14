"""Base exception for all LASO domain errors."""

from typing import Any, Optional


class LasoError(Exception):
    """Base exception with structured error attributes."""

    code: str = "LASO_ERROR"

    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        self.details = details
