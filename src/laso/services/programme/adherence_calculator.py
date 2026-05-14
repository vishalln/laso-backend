"""Adherence calculator — computes medication adherence across check-ins."""

import logging

from laso.utils.db import execute_one

log = logging.getLogger(__name__)


def compute(programme_id: str) -> dict:
    """SUM(doses_taken) / SUM(doses_scheduled) * 100 across all check-ins."""
    log.info("adherence_calculator.compute | programme_id=%s", programme_id)

    row = execute_one(
        """SELECT COALESCE(SUM(doses_taken), 0) AS total_taken,
                  COALESCE(SUM(doses_scheduled), 0) AS total_scheduled
           FROM weekly_check_ins WHERE programme_id = %s""",
        (programme_id,),
    )

    total_taken = row["total_taken"] if row else 0
    total_scheduled = row["total_scheduled"] if row else 0

    if total_scheduled == 0:
        return {"adherence_pct": None, "total_taken": 0, "total_scheduled": 0, "note": "No check-ins recorded"}

    adherence_pct = round((total_taken / total_scheduled) * 100, 1)
    log.info("adherence_calculator.compute | adherence_pct=%s", adherence_pct)
    return {"adherence_pct": adherence_pct, "total_taken": total_taken, "total_scheduled": total_scheduled}
