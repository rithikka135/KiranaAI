from decimal import Decimal

from app.database.connection import SessionLocal
from app.models.product import Product
from app.models.customer import Customer
from app.models.payment import Payment
from app.services.billing_service import (
    create_bill,
    add_bill_item,
    finalize_bill,
)


def sell_product_tool(
    product_name: str,
    quantity: float,
    payment_method: str = "cash",
    customer_name: str = "",
) -> dict:

    allowed_methods = {
        "cash",
        "upi",
        "card",
        "credit",
    }

    if payment_method not in allowed_methods:
        return {
            "success": False,
            "message": (
                f"Invalid payment method: {payment_method}. "
                f"Use cash, upi, card, or credit."
            ),
        }

    db = SessionLocal()

    try:

        # FIND PRODUCT
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

        # FIND CUSTOMER FOR CREDIT SALE
        customer = None

        if payment_method == "credit":

            if not customer_name:
                return {
                    "success": False,
                    "message": (
                        "Credit sale requires a customer name. "
                        "Example: Sell 2 kg rice to Ravi on credit."
                    ),
                }

            customer = (
                db.query(Customer)
                .filter(
                    Customer.name.ilike(f"%{customer_name}%"),
                    Customer.is_active == True,
                )
                .first()
            )

            if customer is None:
                return {
                    "success": False,
                    "message": (
                        f"Customer '{customer_name}' not found."
                    ),
                }

        # CREATE BILL
        bill = create_bill(
            db=db,
            customer_id=customer.id if customer else None,
            payment_method=payment_method,
        )

        # ADD PRODUCT
        add_bill_item(
            db=db,
            bill_id=bill.id,
            product_id=product.id,
            quantity=Decimal(str(quantity)),
        )

        # FINALIZE BILL
        finalized_bill = finalize_bill(
            db=db,
            bill_id=bill.id,
        )

        # RECORD PAYMENT
        # Credit sales are NOT recorded as normal payments.
        if payment_method in {"cash", "upi", "card"}:

            payment = Payment(
                bill_id=finalized_bill.id,
                amount=finalized_bill.total,
                method=payment_method,
            )

            db.add(payment)
            db.commit()

        return {
            "success": True,
            "bill_id": finalized_bill.id,
            "product_name": product.name,
            "quantity": str(quantity),
            "unit": product.unit,
            "subtotal": str(finalized_bill.subtotal),
            "cgst": str(finalized_bill.cgst),
            "sgst": str(finalized_bill.sgst),
            "total": str(finalized_bill.total),
            "payment_method": finalized_bill.payment_method,
            "customer_name": (
                customer.name if customer else None
            ),
            "message": (
                f"Sale completed for {quantity} "
                f"{product.unit} of {product.name}."
            ),
        }

    except ValueError as e:

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()
