"""Order domain model."""

import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, List, Optional

from laso.enums import OrderStatus, ColdChainStatus
from laso.utils.db import execute, execute_one, insert

log = logging.getLogger(__name__)


@dataclass
class Order:
    order_id: str
    patient_id: str
    prescription_id: str
    programme_id: str
    quantity: int = 1
    delivery_address: Optional[str] = None
    status: OrderStatus = OrderStatus.DISPENSED
    carrier_name: Optional[str] = None
    tracking_id: Optional[str] = None
    estimated_delivery: Optional[date] = None
    cold_chain_status: ColdChainStatus = ColdChainStatus.PENDING
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    dispensed_at: Optional[datetime] = None
    packed_at: Optional[datetime] = None
    cold_chain_at: Optional[datetime] = None
    dispatched_at: Optional[datetime] = None
    in_transit_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "order_id": self.order_id,
            "patient_id": self.patient_id,
            "prescription_id": self.prescription_id,
            "programme_id": self.programme_id,
            "quantity": self.quantity,
            "delivery_address": self.delivery_address,
            "status": self.status.value,
            "carrier_name": self.carrier_name,
            "tracking_id": self.tracking_id,
            "estimated_delivery": self.estimated_delivery.isoformat() if self.estimated_delivery else None,
            "cold_chain_status": self.cold_chain_status.value,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "dispensed_at": self.dispensed_at.isoformat() if self.dispensed_at else None,
            "packed_at": self.packed_at.isoformat() if self.packed_at else None,
            "cold_chain_at": self.cold_chain_at.isoformat() if self.cold_chain_at else None,
            "dispatched_at": self.dispatched_at.isoformat() if self.dispatched_at else None,
            "in_transit_at": self.in_transit_at.isoformat() if self.in_transit_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
        }

    @classmethod
    def from_row(cls, row: Dict) -> "Order":
        return cls(
            order_id=row["order_id"],
            patient_id=row["patient_id"],
            prescription_id=row["prescription_id"],
            programme_id=row["programme_id"],
            quantity=row.get("quantity", 1),
            delivery_address=row.get("delivery_address"),
            status=OrderStatus(row["status"]),
            carrier_name=row.get("carrier_name"),
            tracking_id=row.get("tracking_id"),
            estimated_delivery=row.get("estimated_delivery"),
            cold_chain_status=ColdChainStatus(row.get("cold_chain_status", "pending")),
            notes=row.get("notes"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
            dispensed_at=row.get("dispensed_at"),
            packed_at=row.get("packed_at"),
            cold_chain_at=row.get("cold_chain_at"),
            dispatched_at=row.get("dispatched_at"),
            in_transit_at=row.get("in_transit_at"),
            delivered_at=row.get("delivered_at"),
        )

    def save(self) -> None:
        log.info("Order.save | order_id=%s", self.order_id)
        insert(
            """INSERT INTO orders (order_id, patient_id, prescription_id, programme_id,
               quantity, delivery_address, status, carrier_name, tracking_id,
               estimated_delivery, cold_chain_status, notes)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (self.order_id, self.patient_id, self.prescription_id, self.programme_id,
             self.quantity, self.delivery_address, self.status.value, self.carrier_name,
             self.tracking_id, self.estimated_delivery, self.cold_chain_status.value,
             self.notes),
        )
        log.info("Order.save | success | order_id=%s", self.order_id)

    @classmethod
    def get_by_id(cls, order_id: str) -> Optional["Order"]:
        row = execute_one("SELECT * FROM orders WHERE order_id = %s", (order_id,))
        return cls.from_row(row) if row else None

    @classmethod
    def list_for_patient(cls, patient_id: str) -> List["Order"]:
        rows = execute(
            "SELECT * FROM orders WHERE patient_id = %s ORDER BY created_at DESC",
            (patient_id,),
        )
        return [cls.from_row(r) for r in rows]

    @classmethod
    def list_recent(cls, days: int = 30) -> List["Order"]:
        rows = execute(
            "SELECT * FROM orders WHERE created_at >= NOW() - INTERVAL '%s days' ORDER BY created_at DESC",
            (days,),
        )
        return [cls.from_row(r) for r in rows]
