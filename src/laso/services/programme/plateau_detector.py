"""Plateau detector — identifies weight loss stalls from check-in data."""

import logging

from laso.utils.db import execute

log = logging.getLogger(__name__)


def detect(programme_id: str) -> bool:
    """Return True if last 3 check-in weights vary by <= 0.3 kg."""
    log.info("plateau_detector.detect | programme_id=%s", programme_id)

    rows = execute(
        "SELECT weight_kg FROM weekly_check_ins WHERE programme_id = %s ORDER BY week_number DESC LIMIT 3",
        (programme_id,),
    )

    if len(rows) < 3:
        log.info("plateau_detector.detect | fewer than 3 check-ins, returning False")
        return False

    weights = [r["weight_kg"] for r in rows]
    is_plateau = (max(weights) - min(weights)) <= 0.3

    log.info("plateau_detector.detect | weights=%s is_plateau=%s", weights, is_plateau)
    return is_plateau
