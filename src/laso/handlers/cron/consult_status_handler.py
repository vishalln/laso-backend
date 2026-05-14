"""Auto-transition scheduled consultations to in_progress. Runs every 5 minutes."""

import logging

from laso.utils.db import execute

log = logging.getLogger(__name__)

TRANSITION_SQL = """
UPDATE consultations SET status = 'in_progress', updated_at = NOW()
WHERE status = 'scheduled'
  AND scheduled_at <= NOW()
  AND scheduled_at + (duration_minutes || ' minutes')::INTERVAL >= NOW()
RETURNING consultation_id
"""


def lambda_handler(event, context):
    """Auto-transition scheduled consultations to in_progress when within time window."""
    rows = execute(TRANSITION_SQL)
    count = len(rows)

    log.info("consult_status_handler | action=transitioned_consultations count=%d", count)
    return {"consultations_transitioned": count}
