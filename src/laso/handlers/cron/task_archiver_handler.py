"""Archive tasks in 'done' status for 7+ days. Runs daily 02:00 IST."""

import logging

from laso.utils.db import execute

log = logging.getLogger(__name__)

ARCHIVE_SQL = """
UPDATE tasks SET status = 'archived'
WHERE status = 'done' AND completed_at < NOW() - INTERVAL '7 days'
RETURNING task_id
"""


def lambda_handler(event, context):
    """Archive tasks in 'done' status for 7+ days."""
    rows = execute(ARCHIVE_SQL)
    count = len(rows)

    log.info("task_archiver_handler | action=archived_tasks count=%d", count)
    return {"tasks_archived": count}
