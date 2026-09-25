from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.product import Product


def create_product(
    db: Session,
    sku: str,
    name: str,
    category: str,
    unit: str,
    selling_price: Decimal,
    cost_price: Decimal,
    gst_rate: Decimal,
    hsn_code: str | None = None,
) -> Product:

    product = Product(
        sku=sku,
        name=name,
        category=category,
        unit=unit,
        selling_price=selling_price,
        cost_price=cost_price,
        gst_rate=gst_rate,
        hsn_code=hsn_code,
        is_active=True,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product