from decimal import Decimal

from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models.product import Product
from app.models.inventory import Inventory


def check_stock(
    db: Session,
    product_name: str,
) -> dict:

    product = (
        db.query(Product)
        .filter(
            Product.name.ilike(f"%{product_name}%"),
            Product.is_active == True,
        )
        .first()
    )

    if product is None:
        return {
            "success": False,
            "message": f"Product '{product_name}' not found.",
        }

    inventory = (
        db.query(Inventory)
        .filter(Inventory.product_id == product.id)
        .first()
    )

    if inventory is None:
        return {
            "success": False,
            "message": f"No inventory record found for {product.name}.",
        }

    return {
        "success": True,
        "product_id": product.id,
        "product_name": product.name,
        "quantity": str(inventory.quantity),
        "unit": product.unit,
        "reorder_level": str(inventory.reorder_level),
        "cost_price": str(product.cost_price),
        "selling_price": str(product.selling_price),
        "gst_rate": str(product.gst_rate),
        "hsn_code": product.hsn_code,
    }


def receive_stock_tool(
    product_name: str,
    quantity: float,
    cost_price: float | None = None,
    selling_price: float | None = None,
) -> dict:

    db = SessionLocal()

    try:
        # --------------------------------------------------
        # 1. Find product
        # --------------------------------------------------

        product = (
            db.query(Product)
            .filter(
                Product.name.ilike(f"%{product_name}%"),
                Product.is_active == True,
            )
            .first()
        )

        if product is None:
            return {
                "success": False,
                "message": f"Product '{product_name}' not found.",
            }

        # --------------------------------------------------
        # 2. Convert values to Decimal
        # --------------------------------------------------

        quantity_decimal = Decimal(str(quantity))

        if cost_price is not None:
            cost_price_decimal = Decimal(str(cost_price))
        else:
            cost_price_decimal = None

        if selling_price is not None:
            selling_price_decimal = Decimal(
                str(selling_price)
            )
        else:
            selling_price_decimal = None

        # --------------------------------------------------
        # 3. Validate quantity
        # --------------------------------------------------

        if quantity_decimal <= 0:
            return {
                "success": False,
                "message": (
                    "Received quantity must be greater "
                    "than zero."
                ),
            }

        # --------------------------------------------------
        # 4. Validate cost price
        # --------------------------------------------------

        if (
            cost_price_decimal is not None
            and cost_price_decimal <= 0
        ):
            return {
                "success": False,
                "message": (
                    "Cost price must be greater than zero."
                ),
            }

        # --------------------------------------------------
        # 5. Validate selling price / MRP
        # --------------------------------------------------

        if (
            selling_price_decimal is not None
            and selling_price_decimal <= 0
        ):
            return {
                "success": False,
                "message": (
                    "Selling price must be greater than zero."
                ),
            }

        # --------------------------------------------------
        # 6. Use existing prices if new prices not supplied
        # --------------------------------------------------

        effective_cost_price = (
            cost_price_decimal
            if cost_price_decimal is not None
            else product.cost_price
        )

        effective_selling_price = (
            selling_price_decimal
            if selling_price_decimal is not None
            else product.selling_price
        )

        # --------------------------------------------------
        # 7. Prevent selling below cost
        # --------------------------------------------------

        if effective_selling_price < effective_cost_price:
            return {
                "success": False,
                "message": (
                    "Selling price cannot be lower "
                    "than cost price."
                ),
            }

        # --------------------------------------------------
        # 8. Update product prices
        # --------------------------------------------------

        if cost_price_decimal is not None:
            product.cost_price = cost_price_decimal

        if selling_price_decimal is not None:
            product.selling_price = selling_price_decimal

        # --------------------------------------------------
        # 9. Find inventory
        # --------------------------------------------------

        inventory = (
          db.query(Inventory)
        .filter(
            Inventory.product_id == product.id
        )
        .with_for_update()
        .first()
)

        # --------------------------------------------------
        # 10. Create inventory if it doesn't exist
        # --------------------------------------------------

        if inventory is None:
            inventory = Inventory(
                product_id=product.id,
                quantity=Decimal("0"),
                reorder_level=Decimal("5"),
            )

            db.add(inventory)

        # --------------------------------------------------
        # 11. Add received quantity
        # --------------------------------------------------

        inventory.quantity += quantity_decimal

        # --------------------------------------------------
        # 12. Save everything
        # --------------------------------------------------

        db.commit()
        db.refresh(inventory)
        db.refresh(product)

        return {
            "success": True,
            "message": (
                f"Received {quantity_decimal} "
                f"{product.unit} of {product.name}."
            ),
            "product_id": product.id,
            "product_name": product.name,
            "quantity_received": str(
                quantity_decimal
            ),
            "current_stock": str(
                inventory.quantity
            ),
            "unit": product.unit,
            "cost_price": str(
                product.cost_price
            ),
            "selling_price": str(
                product.selling_price
            ),
            "gst_rate": str(
                product.gst_rate
            ),
            "hsn_code": product.hsn_code,
        }

    except ValueError as e:

        db.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    except Exception as e:

        db.rollback()

        return {
            "success": False,
            "message": (
                f"Unable to receive stock: {str(e)}"
            ),
        }

    finally:
        db.close()