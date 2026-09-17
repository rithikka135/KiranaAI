from decimal import Decimal

from app.database.connection import SessionLocal
from app.models.product import Product


products = [
    {
        "sku": "RICE001",
        "name": "India Gate Basmati Rice",
        "category": "Groceries",
        "unit": "kg",
        "selling_price": Decimal("75.00"),
        "cost_price": Decimal("60.00"),
        "gst_rate": Decimal("5.00"),
    },
    {
        "sku": "SUGAR001",
        "name": "White Sugar",
        "category": "Groceries",
        "unit": "kg",
        "selling_price": Decimal("48.00"),
        "cost_price": Decimal("42.00"),
        "gst_rate": Decimal("5.00"),
    },
    {
        "sku": "OIL001",
        "name": "Fortune Sunflower Oil",
        "category": "Cooking Oil",
        "unit": "litre",
        "selling_price": Decimal("145.00"),
        "cost_price": Decimal("125.00"),
        "gst_rate": Decimal("5.00"),
    },
    {
        "sku": "MILK001",
        "name": "Aavin Full Cream Milk",
        "category": "Dairy",
        "unit": "litre",
        "selling_price": Decimal("60.00"),
        "cost_price": Decimal("52.00"),
        "gst_rate": Decimal("5.00"),
    },
    {
        "sku": "DAL001",
        "name": "Toor Dal",
        "category": "Pulses",
        "unit": "kg",
        "selling_price": Decimal("140.00"),
        "cost_price": Decimal("120.00"),
        "gst_rate": Decimal("5.00"),
    },
    {
        "sku": "SOAP001",
        "name": "Dove Bath Soap",
        "category": "Personal Care",
        "unit": "piece",
        "selling_price": Decimal("55.00"),
        "cost_price": Decimal("42.00"),
        "gst_rate": Decimal("18.00"),
    },
    {
        "sku": "BISCUIT001",
        "name": "Parle-G Biscuits",
        "category": "Snacks",
        "unit": "packet",
        "selling_price": Decimal("10.00"),
        "cost_price": Decimal("8.00"),
        "gst_rate": Decimal("5.00"),
    },
    {
        "sku": "TEA001",
        "name": "Tata Tea",
        "category": "Beverages",
        "unit": "packet",
        "selling_price": Decimal("120.00"),
        "cost_price": Decimal("105.00"),
        "gst_rate": Decimal("5.00"),
    },
]


def seed_products():
    db = SessionLocal()

    try:
        for data in products:

            existing_product = (
                db.query(Product)
                .filter(Product.sku == data["sku"])
                .first()
            )

            if existing_product:
                print(f"Already exists: {data['name']}")
                continue

            product = Product(
                **data,
                is_active=True,
            )

            db.add(product)

        db.commit()

        print("Product seeding completed successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_products()