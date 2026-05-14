"""Error messages, success messages, and task title templates."""

from typing import Final

# ── Error messages ───────────────────────────────────────────────────────────
ERRORS: Final[dict] = {
    "NOT_FOUND": "Resource not found",
    "VALIDATION": "Validation failed",
    "CONFLICT": "Resource conflict",
    "FORBIDDEN": "You do not have permission to perform this action",
    "UNAUTHORIZED": "Authentication required",
    "INTERNAL": "An internal error occurred",
    "INVALID_TRANSITION": "Invalid status transition",
    "ALREADY_EXISTS": "Resource already exists",
    "QUIZ_NOT_FOUND": "Quiz submission not found",
    "QUIZ_ALREADY_CLAIMED": "Quiz submission has already been claimed",
}

# ── Success messages ─────────────────────────────────────────────────────────
SUCCESS: Final[dict] = {
    "CREATED": "Resource created successfully",
    "UPDATED": "Resource updated successfully",
    "DELETED": "Resource deleted successfully",
    "ARCHIVED": "Resource archived successfully",
}

# ── Task title templates (use .format(patient_name=...)) ─────────────────────
TASK_TITLES: Final[dict] = {
    "schedule_consultation": "Schedule consultation for {patient_name}",
    "missed_check_in": "Missed check-in: {patient_name}",
    "refill_request": "Refill request from {patient_name}",
    "enter_blood_results": "Enter blood results for {patient_name}",
    "create_order": "Create order for {patient_name}",
    "escalation": "Escalation: {patient_name}",
    "follow_up": "Follow-up needed: {patient_name}",
    "reschedule_no_show": "Reschedule no-show: {patient_name}",
}
