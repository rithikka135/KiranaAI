from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.inventory import Inventory


def receive_stock(
    db: Session,
    product_name: str,
    quantity: Decimal,
    session_key: str = "default_owner",
):
    product_name = product_name.strip()

    if not product_name:
        raise ValueError("Product name cannot be empty.")

    if quantity <= 0:
        raise ValueError("Received quantity must be greater than zero.")

    # Find active product
    product = (
        db.query(Product)
        .filter(
            Product.name.ilike(product_name),
            Product.is_active == True,
        )
        .first()
    )

    if product is None:
        # Try partial match
        product = (
            db.query(Product)
            .filter(
                Product.name.ilike(f"%{product_name}%"),
                Product.is_active == True,
            )
            .first()
        )

    if product is None:
        raise ValueError(
            f"Product '{product_name}' was not found."
        )

    # Lock inventory row
    inventory = (
        db.query(Inventory)
        .filter(Inventory.product_id == product.id)
        .with_for_update()
        .first()
    )

    if inventory is None:
        inventory = Inventory(
            product_id=product.id,
            quantity=Decimal("0.000"),
            reorder_level=Decimal("5.000"),
        )
        db.add(inventory)
        db.flush()

    inventory.quantity += quantity

    db.commit()
    db.refresh(inventory)

    return {
        "success": True,
        "product_id": product.id,
        "product_name": product.name,
        "quantity_received": str(quantity),
        "current_stock": str(inventory.quantity),
        "unit": product.unit,
        "message": (
            f"Added {quantity} {product.unit} of "
            f"{product.name}. "
            f"Current stock: {inventory.quantity} {product.unit}."
        ),
    }


def get_inventory(
    db: Session,
    product_name: str | None = None,
):
    query = (
        db.query(Product, Inventory)
        .join(Inventory, Product.id == Inventory.product_id)
        .filter(Product.is_active == True)
    )

    if product_name:
        query = query.filter(
            Product.name.ilike(f"%{product_name.strip()}%")
        )

    rows = query.order_by(Product.name).all()

    results = []

    for product, inventory in rows:
        results.append(
            {
                "product_id": product.id,
                "product_name": product.name,
                "sku": product.sku,
                "category": product.category,
                "quantity": str(inventory.quantity),
                "reorder_level": str(inventory.reorder_level),
                "unit": product.unit,
                "low_stock": inventory.quantity <= inventory.reorder_level,
            }
        )

    return results


def get_low_stock(
    db: Session,
):
    rows = (
        db.query(Product, Inventory)
        .join(Inventory, Product.id == Inventory.product_id)
        .filter(
            Product.is_active == True,
            Inventory.quantity <= Inventory.reorder_level,
        )
        .order_by(Inventory.quantity.asc())
        .all()
    )

    results = []

    for product, inventory in rows:
        results.append(
            {
                "product_id": product.id,
                "product_name": product.name,
                "quantity": str(inventory.quantity),
                "reorder_level": str(inventory.reorder_level),
                "unit": product.unit,
            }
        )

    return results