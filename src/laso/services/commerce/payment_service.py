"""Payment service — STUB for Phase 1 (no real payment gateway)."""

import logging
from datetime import datetime
from uuid import uuid4

from laso.enums.payment import PaymentStatus
from laso.exceptions import NotFoundError
from laso.models.payment import Payment

log = logging.getLogger(__name__)


def initiate(programme_id: str, patient_id: str, amount: float) -> dict:
    """Create payment record and immediately mark as COMPLETED (stub)."""
    log.info("payment_service.initiate | programme_id=%s patient_id=%s amount=%s", programme_id, patient_id, amount)

    payment = Payment(
        payment_id=str(uuid4()),
        programme_id=programme_id,
        patient_id=patient_id,
        amount=amount,
        status=PaymentStatus.COMPLETED,
        completed_at=datetime.utcnow().isoformat(),
    )
    payment.save()

    result = {"payment_id": payment.payment_id, "status": payment.status, "completed_at": payment.completed_at}
    log.info("payment_service.initiate | payment_id=%s", payment.payment_id)
    return result


def get_status(payment_id: str) -> dict:
    """Get payment status by ID."""
    log.info("payment_service.get_status | payment_id=%s", payment_id)
    payment = Payment.get_by_id(payment_id)
    if not payment:
        raise NotFoundError("Payment not found")
    return payment.to_dict()
