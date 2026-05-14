"""Blood test service — result entry and queries."""

import logging

from laso.enums.blood_test import BloodTestStatus
from laso.exceptions import NotFoundError, ValidationError
from laso.models.blood_test import BloodTest
from laso.utils.validation import validate_transition

log = logging.getLogger(__name__)


def enter_results(blood_test_id: str, results: dict, entered_by: str) -> dict:
    """Validate, save results, transition to RESULTS_READY, complete programme step."""
    log.info("blood_test_service.enter_results | blood_test_id=%s entered_by=%s", blood_test_id, entered_by)

    bt = BloodTest.get_by_id(blood_test_id)
    if not bt:
        raise NotFoundError("Blood test not found")

    validate_transition(bt.status, BloodTestStatus.RESULTS_READY, BloodTestStatus)

    # Update results via SQL (record already exists)
    from laso.utils.db import execute as db_exec
    fields = {k: v for k, v in results.items()
              if k in ("hba1c", "fasting_glucose", "total_cholesterol", "ldl", "hdl",
                       "triglycerides", "tsh", "creatinine", "alt", "ast") and v is not None}
    fields["entered_by"] = entered_by
    fields["status"] = BloodTestStatus.RESULTS_READY.value
    fields["results_at"] = "NOW()"

    set_clause = ", ".join(f"{k} = %s" if k != "results_at" else f"{k} = NOW()" for k in fields)
    values = [v for k, v in fields.items() if k != "results_at"]
    values.append(blood_test_id)
    db_exec(f"UPDATE blood_tests SET {set_clause} WHERE blood_test_id = %s", tuple(values))
    bt.status = BloodTestStatus.RESULTS_READY

    # Complete associated programme step
    if bt.programme_step_id and bt.programme_id:
        from laso.services.programme_service import complete_step
        complete_step(bt.programme_id, bt.programme_step_id)

    log.info("blood_test_service.enter_results | done blood_test_id=%s", blood_test_id)
    return bt.to_dict()


def get_by_id(blood_test_id: str) -> dict:
    """Get blood test by ID or raise NotFoundError."""
    log.info("blood_test_service.get_by_id | blood_test_id=%s", blood_test_id)
    bt = BloodTest.get_by_id(blood_test_id)
    if not bt:
        raise NotFoundError("Blood test not found")
    return bt.to_dict()


def list_for_programme(programme_id: str) -> list:
    """List all blood tests for a programme."""
    log.info("blood_test_service.list_for_programme | programme_id=%s", programme_id)
    return [bt.to_dict() for bt in BloodTest.list_for_programme(programme_id)]
