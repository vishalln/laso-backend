"""Flag evaluator — auto-creates patient flags after check-in submission."""

import logging

from laso.services.adherence_calculator import compute as compute_adherence
from laso.services.plateau_detector import detect as detect_plateau
from laso.services.flag_service import set_flag

log = logging.getLogger(__name__)

ADHERENCE_THRESHOLD = 60


def evaluate_after_checkin(patient_id: str, programme_id: str, check_in_data: dict) -> list:
    """Evaluate auto-flag rules after a check-in. Returns list of flags created."""
    log.info("flag_evaluator.evaluate_after_checkin | patient_id=%s", patient_id)
    created_flags = []

    # Rule 1: adherence below threshold
    adherence = compute_adherence(programme_id)
    if adherence["adherence_pct"] is not None and adherence["adherence_pct"] < ADHERENCE_THRESHOLD:
        flag = set_flag(patient_id, "adherence_risk", "Adherence below 60%", "system")
        if flag:
            created_flags.append(flag)

    # Rule 2: weight plateau detected
    if detect_plateau(programme_id):
        flag = set_flag(patient_id, "plateau", "Weight plateau detected (3 weeks)", "system")
        if flag:
            created_flags.append(flag)

    # Rule 3: severe side effects
    side_effects = check_in_data.get("side_effects") or []
    has_severe = any(se.get("severity") == "severe" for se in side_effects)
    if has_severe:
        flag = set_flag(patient_id, "review_needed", "Severe side effect reported", "system")
        if flag:
            created_flags.append(flag)

    log.info("flag_evaluator.evaluate_after_checkin | flags_created=%d", len(created_flags))
    return created_flags
