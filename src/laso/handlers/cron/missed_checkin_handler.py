"""Detect patients who missed their weekly check-in. Runs Monday 00:30 IST."""

import logging
from datetime import date

from laso.constants.messages import TASK_TITLES
from laso.services import task_service
from laso.utils.db import execute

log = logging.getLogger(__name__)

MISSED_CHECKIN_SQL = """
SELECT p.patient_id, p.name, prog.programme_id
FROM patients p
JOIN programmes prog ON p.patient_id = prog.patient_id AND prog.status = 'active'
JOIN programme_steps ps ON prog.programme_id = ps.programme_id
    AND ps.step_type = 'check_in' AND ps.status = 'active'
WHERE NOT EXISTS (
    SELECT 1 FROM weekly_check_ins ci
    WHERE ci.patient_id = p.patient_id
      AND ci.programme_id = prog.programme_id
      AND EXTRACT(ISOYEAR FROM ci.submitted_at) = EXTRACT(ISOYEAR FROM NOW() - INTERVAL '7 days')
      AND EXTRACT(WEEK FROM ci.submitted_at) = EXTRACT(WEEK FROM NOW() - INTERVAL '7 days')
)
"""


def lambda_handler(event, context):
    """Detect patients who missed weekly check-in last week, create tasks."""
    rows = execute(MISSED_CHECKIN_SQL)

    for row in rows:
        title = TASK_TITLES["missed_check_in"].format(patient_name=row["name"])
        task_service.create_task(
            patient_id=row["patient_id"],
            task_type="missed_check_in",
            title=title,
            priority="medium",
            due_date=date.today().isoformat(),
        )

    log.info("missed_checkin_handler | action=created_tasks count=%d", len(rows))
    return {"tasks_created": len(rows)}
