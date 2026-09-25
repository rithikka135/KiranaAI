from decimal import Decimal

from app.database.connection import SessionLocal
from app.services.product_service import create_product


def create_product_tool(
    name: str,
    category: str,
    unit: str,
    selling_price: float,
    cost_price: float,
    gst_rate: float,
    hsn_code: str,
) -> dict:

    db = SessionLocal()

    try:
        # Generate SKU automatically from product name
        sku = name.upper().replace(" ", "_")

        product = create_product(
            db=db,
            sku=sku,
            name=name,
            category=category,
            unit=unit,
            selling_price=Decimal(str(selling_price)),
            cost_price=Decimal(str(cost_price)),
            gst_rate=Decimal(str(gst_rate)),
            hsn_code=hsn_code,
        )

        return {
            "success": True,
            "product_id": product.id,
            "sku": product.sku,
            "name": product.name,
            "category": product.category,
            "unit": product.unit,
            "selling_price": str(product.selling_price),
            "cost_price": str(product.cost_price),
            "gst_rate": str(product.gst_rate),
            "hsn_code": product.hsn_code,
        }

    except Exception as e:

        db.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()