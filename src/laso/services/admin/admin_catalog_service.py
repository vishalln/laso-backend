"""Admin catalog management service."""

import logging
from uuid import uuid4

from laso.enums import ProductCategory
from laso.exceptions import ConflictError, NotFoundError
from laso.models.catalog import CatalogProduct
from laso.utils.db import execute, update_by_id, delete_by_id

log = logging.getLogger(__name__)


def list_all() -> list:
    """List all catalog products."""
    log.info("admin_catalog_service.list_all")
    return [p.to_dict() for p in CatalogProduct.list_all()]


def list_medications() -> list:
    """List in-stock prescription medications only."""
    log.info("admin_catalog_service.list_medications")
    return [p.to_dict() for p in CatalogProduct.list_medications()]


def create(body: dict) -> dict:
    """Create a catalog product."""
    log.info("admin_catalog_service.create | name=%s", body.get("name"))
    product = CatalogProduct(
        product_id=str(uuid4()),
        name=body["name"],
        brand=body["brand"],
        category=ProductCategory(body["category"]),
        unit=body["unit"],
        tagline=body.get("tagline"),
        emoji=body.get("emoji"),
        price_inr=body.get("price_inr", 0),
        recommended_weeks=body.get("recommended_weeks", 0),
        clinical_rationale=body.get("clinical_rationale"),
        stock_count=body.get("stock_count", 0),
        in_stock=body.get("in_stock", True),
        requires_prescription=body.get("requires_prescription", False),
    )
    product.save()
    return product.to_dict()


def update(product_id: str, body: dict) -> dict:
    """Update a catalog product."""
    log.info("admin_catalog_service.update | product_id=%s", product_id)
    product = CatalogProduct.get_by_id(product_id)
    if not product:
        raise NotFoundError("Product not found")
    allowed = {"name", "brand", "category", "unit", "tagline", "emoji", "price_inr",
               "recommended_weeks", "clinical_rationale", "stock_count", "in_stock",
               "requires_prescription"}
    fields = {k: v for k, v in body.items() if k in allowed}
    update_by_id("catalog_products", "product_id", product_id, **fields)
    return CatalogProduct.get_by_id(product_id).to_dict()


def delete(product_id: str) -> dict:
    """Delete product if not referenced in active prescriptions."""
    log.info("admin_catalog_service.delete | product_id=%s", product_id)
    product = CatalogProduct.get_by_id(product_id)
    if not product:
        raise NotFoundError("Product not found")

    refs = execute(
        "SELECT COUNT(*) as cnt FROM prescriptions WHERE product_id = %s AND status = 'active'",
        (product_id,),
    )
    if refs and refs[0]["cnt"] > 0:
        raise ConflictError("Product is referenced in active prescriptions")

    delete_by_id("catalog_products", "product_id", product_id)
    return {"deleted": True, "product_id": product_id}


def toggle_stock(product_id: str) -> dict:
    """Toggle in_stock status."""
    log.info("admin_catalog_service.toggle_stock | product_id=%s", product_id)
    product = CatalogProduct.get_by_id(product_id)
    if not product:
        raise NotFoundError("Product not found")
    new_status = not product.in_stock
    update_by_id("catalog_products", "product_id", product_id, in_stock=new_status)
    return {**product.to_dict(), "in_stock": new_status}
