"""Programme domain constants."""

from typing import Final

DEFAULT_TEMPLATE_NAME: Final[str] = "standard_glp1"
PAYMENT_AMOUNT_INR: Final[int] = 14999

MSG_PROGRAMME_CREATED: Final[str] = "Programme created successfully"
MSG_PROGRAMME_ACTIVATED: Final[str] = "Programme activated successfully"
MSG_STEP_COMPLETED: Final[str] = "Step marked as completed"
MSG_STEP_SKIPPED: Final[str] = "Step skipped"
MSG_INVALID_STEP_TRANSITION: Final[str] = "Invalid step status transition"
MSG_INVALID_PROGRAMME_TRANSITION: Final[str] = "Invalid programme status transition"
