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
) -> Product:

    product = Product(
        sku=sku,
        name=name,
        category=category,
        unit=unit,
        selling_price=selling_price,
        cost_price=cost_price,
        gst_rate=gst_rate,
        is_active=True,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product