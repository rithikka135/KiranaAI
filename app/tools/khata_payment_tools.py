from decimal import Decimal

from app.database.connection import SessionLocal
from app.models.customer import Customer
from app.services.khata_service import record_khata_payment


def record_customer_payment(
    customer_name: str,
    amount: float,
) -> dict:

    db = SessionLocal()

    try:

        if amount <= 0:
            return {
                "success": False,
                "message": (
                    "Payment amount must be greater than zero."
                ),
            }

        customer = (
            db.query(Customer)
            .filter(
                Customer.name.ilike(
                    f"%{customer_name}%"
                ),
                Customer.is_active == True,
            )
            .first()
        )

        if customer is None:
            return {
                "success": False,
                "message": (
                    f"Customer '{customer_name}' "
                    f"not found."
                ),
            }

        payment = record_khata_payment(
            db=db,
            customer_id=customer.id,
            amount=Decimal(str(amount)),
            note="Khata payment",
        )

        return {
            "success": True,
            "customer_id": customer.id,
            "customer_name": customer.name,
            "amount": str(payment.amount),
            "message": (
                f"₹{payment.amount} payment recorded "
                f"for {customer.name}."
            ),
        }

    except ValueError as e:

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()
