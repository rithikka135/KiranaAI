from decimal import Decimal

from app.database.connection import SessionLocal
from app.models.product import Product
from app.services.inventory_service import sell_stock


db = SessionLocal()

try:
    product = (
        db.query(Product)
        .filter(Product.sku == "RICE001")
        .first()
    )

    if product is None:
        raise ValueError("Rice product not found.")

    inventory = sell_stock(
        db=db,
        product_id=product.id,
        quantity=Decimal("10000"),
    )

    print("Stock sold successfully!")
    print("Product:", product.name)
    print("Remaining stock:", inventory.quantity)

except ValueError as error:
    print("Sale failed:", error)

finally:
    db.close()