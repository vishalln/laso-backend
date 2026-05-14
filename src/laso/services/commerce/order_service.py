"""Order service — STUB for Phase 1 (no real fulfilment pipeline)."""

import logging
from uuid import uuid4

from laso.exceptions import NotFoundError
from laso.utils.db import execute, execute_one, insert
from laso.utils.validation import validate_required

log = logging.getLogger(__name__)

_SQL_CREATE = """
    INSERT INTO orders (order_id, patient_id, prescription_id, programme_id, quantity, delivery_address, status, notes)
    VALUES (%s, %s, %s, %s, %s, %s, 'dispensed', %s)
"""

_SQL_GET_BY_ID = "SELECT * FROM orders WHERE order_id = %s"
_SQL_LIST_FOR_PATIENT = "SELECT * FROM orders WHERE patient_id = %s ORDER BY created_at DESC"
_SQL_LIST_RECENT = "SELECT * FROM orders WHERE created_at >= NOW() - INTERVAL '30 days' ORDER BY created_at DESC"


def create(body: dict) -> dict:
    log.info("order_service.create | patient_id=%s", body.get("patient_id"))

    validate_required(body, ["patient_id"])

    order_id = str(uuid4())
    params = (
        order_id,
        body["patient_id"],
        body.get("prescription_id"),
        body.get("programme_id"),
        body.get("quantity", 1),
        body.get("delivery_address"),
        body.get("notes"),
    )
    insert(_SQL_CREATE, params)

    row = execute_one(_SQL_GET_BY_ID, (order_id,))
    log.info("order_service.create | success | order_id=%s", order_id)
    return row


def advance(order_id: str, body: dict) -> dict:
    log.info("order_service.advance | order_id=%s target=%s", order_id, body.get("status"))

    row = execute_one(_SQL_GET_BY_ID, (order_id,))
    if not row:
        raise NotFoundError("Order not found")

    target = body.get("status")
    execute(
        "UPDATE orders SET status = %s, updated_at = NOW() WHERE order_id = %s",
        (target, order_id),
    )

    row = execute_one(_SQL_GET_BY_ID, (order_id,))
    log.info("order_service.advance | success | order_id=%s new_status=%s", order_id, target)
    return row


def list_for_patient(patient_id: str) -> list:
    log.info("order_service.list_for_patient | patient_id=%s", patient_id)
    rows = execute(_SQL_LIST_FOR_PATIENT, (patient_id,))
    log.info("order_service.list_for_patient | count=%d", len(rows))
    return rows


def list_recent() -> list:
    log.info("order_service.list_recent")
    rows = execute(_SQL_LIST_RECENT)
    log.info("order_service.list_recent | count=%d", len(rows))
    return rows
