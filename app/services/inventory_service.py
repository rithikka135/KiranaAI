from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.inventory import Inventory


def receive_stock(
    db: Session,
    product_id: int,
    quantity: Decimal,
) -> Inventory:
    # 1. Validate quantity
    if quantity <= 0:
        raise ValueError("Received quantity must be greater than zero.")

    # 2. Check that the product exists
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if product is None:
        raise ValueError("Product not found.")

    # 3. Check that the product is active
    if not product.is_active:
        raise ValueError("Cannot receive stock for an inactive product.")

    # 4. Find the inventory record
    inventory = (
        db.query(Inventory)
        .filter(Inventory.product_id == product_id)
        .first()
    )

    # 5. Create inventory record if it doesn't exist
    if inventory is None:
        inventory = Inventory(
            product_id=product_id,
            quantity=Decimal("0"),
            reorder_level=Decimal("5"),
        )
        db.add(inventory)

    # 6. Add the received stock
    inventory.quantity += quantity

    # 7. Save changes
    db.commit()
    db.refresh(inventory)

    return inventory

def sell_stock(
    db: Session,
    product_id: int,
    quantity: Decimal,
) -> Inventory:
    # 1. Validate quantity
    if quantity <= 0:
        raise ValueError("Sold quantity must be greater than zero.")

    # 2. Find the product
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if product is None:
        raise ValueError("Product not found.")

    # 3. Check product status
    if not product.is_active:
        raise ValueError("Cannot sell an inactive product.")

    # 4. Find inventory
    inventory = (
        db.query(Inventory)
        .filter(Inventory.product_id == product_id)
        .first()
    )

    if inventory is None:
        raise ValueError("Inventory record not found.")

    # 5. Prevent overselling
    if inventory.quantity < quantity:
        raise ValueError(
            f"Insufficient stock. "
            f"Available: {inventory.quantity}, "
            f"Requested: {quantity}"
        )

    # 6. Reduce stock
    inventory.quantity -= quantity

    # 7. Save changes
    db.commit()
    db.refresh(inventory)

    return inventory