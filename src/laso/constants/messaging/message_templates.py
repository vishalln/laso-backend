"""Coordinator quick-message templates with {patient_name} placeholder."""

from typing import Final

MISSED_DOSE: Final[str] = (
    "Hi {patient_name}, we noticed you may have missed a dose. "
    "Please take it as soon as you remember, or skip if it's close to your next one. "
    "Let us know if you need help."
)

NO_CHECK_IN: Final[str] = (
    "Hi {patient_name}, we haven't heard from you in a while. "
    "A quick check-in helps us track your progress and adjust your plan. "
    "Please log your weight and symptoms when you can."
)

WEIGHT_STALLED: Final[str] = (
    "Hi {patient_name}, your weight has plateaued recently. "
    "This is common and doesn't mean the programme isn't working. "
    "We may review your dose at your next consultation."
)

NAUSEA_SUPPORT: Final[str] = (
    "Hi {patient_name}, nausea is one of the most common side effects and usually improves. "
    "Try eating smaller meals, staying hydrated, and avoiding fatty foods. "
    "If it persists beyond a week, let your doctor know."
)

QUICK_MESSAGES: Final[dict] = {
    "missed_dose": MISSED_DOSE,
    "no_check_in": NO_CHECK_IN,
    "weight_stalled": WEIGHT_STALLED,
    "nausea_support": NAUSEA_SUPPORT,
}
