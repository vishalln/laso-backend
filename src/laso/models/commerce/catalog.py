"""Catalog product domain model."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from laso.enums import ProductCategory
from laso.utils.db import execute, execute_one, insert

log = logging.getLogger(__name__)


@dataclass
class CatalogProduct:
    product_id: str
    name: str
    brand: str
    category: ProductCategory
    unit: str
    tagline: Optional[str] = None
    emoji: Optional[str] = None
    price_inr: float = 0.0
    recommended_weeks: int = 0
    clinical_rationale: Optional[str] = None
    stock_count: int = 0
    in_stock: bool = True
    requires_prescription: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "product_id": self.product_id,
            "name": self.name,
            "brand": self.brand,
            "category": self.category.value,
            "unit": self.unit,
            "tagline": self.tagline,
            "emoji": self.emoji,
            "price_inr": self.price_inr,
            "recommended_weeks": self.recommended_weeks,
            "clinical_rationale": self.clinical_rationale,
            "stock_count": self.stock_count,
            "in_stock": self.in_stock,
            "requires_prescription": self.requires_prescription,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_row(cls, row: Dict) -> "CatalogProduct":
        return cls(
            product_id=row["product_id"],
            name=row["name"],
            brand=row["brand"],
            category=ProductCategory(row["category"]),
            unit=row["unit"],
            tagline=row.get("tagline"),
            emoji=row.get("emoji"),
            price_inr=row.get("price_inr", 0.0),
            recommended_weeks=row.get("recommended_weeks", 0),
            clinical_rationale=row.get("clinical_rationale"),
            stock_count=row.get("stock_count", 0),
            in_stock=row.get("in_stock", True),
            requires_prescription=row.get("requires_prescription", False),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def save(self) -> None:
        log.info("CatalogProduct.save | product_id=%s", self.product_id)
        insert(
            """INSERT INTO catalog_products (product_id, name, brand, category, unit, tagline,
               emoji, price_inr, recommended_weeks, clinical_rationale, stock_count,
               in_stock, requires_prescription)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (self.product_id, self.name, self.brand, self.category.value, self.unit,
             self.tagline, self.emoji, self.price_inr, self.recommended_weeks,
             self.clinical_rationale, self.stock_count, self.in_stock,
             self.requires_prescription),
        )

    @classmethod
    def get_by_id(cls, product_id: str) -> Optional["CatalogProduct"]:
        row = execute_one("SELECT * FROM catalog_products WHERE product_id = %s", (product_id,))
        return cls.from_row(row) if row else None

    @classmethod
    def list_all(cls) -> List["CatalogProduct"]:
        rows = execute("SELECT * FROM catalog_products ORDER BY name")
        return [cls.from_row(r) for r in rows]

    @classmethod
    def list_medications(cls) -> List["CatalogProduct"]:
        rows = execute(
            "SELECT * FROM catalog_products WHERE in_stock = true AND requires_prescription = true ORDER BY name"
        )
        return [cls.from_row(r) for r in rows]
