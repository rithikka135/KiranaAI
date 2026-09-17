from decimal import Decimal

from app.database.connection import SessionLocal
from app.models.product import Product
from app.services.inventory_service import receive_stock


db = SessionLocal()

try:
    product = (
        db.query(Product)
        .filter(Product.sku == "RICE001")
        .first()
    )

    if product is None:
        raise ValueError("Rice product not found.")

    inventory = receive_stock(
        db=db,
        product_id=product.id,
        quantity=Decimal("25"),
    )

    print("Stock received successfully!")
    print("Product:", product.name)
    print("Current stock:", inventory.quantity)

finally:
    db.close()