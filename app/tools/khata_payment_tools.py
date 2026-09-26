from decimal import Decimal, InvalidOperation

from app.database.connection import SessionLocal
from app.models.customer import Customer
from app.services.khata_service import record_khata_payment


def record_customer_payment(
    customer_name: str,
    amount,
) -> dict:

    db = SessionLocal()

    try:

        # ========================================================
        # CONVERT PAYMENT AMOUNT TO DECIMAL
        # Ollama may send the amount as a string such as "200".
        # ========================================================

        try:

            payment_amount = Decimal(
                str(amount).strip()
            )

        except (InvalidOperation, ValueError):

            return {
                "success": False,
                "message": (
                    f"Invalid payment amount: {amount}"
                ),
            }


        # ========================================================
        # VALIDATE PAYMENT AMOUNT
        # ========================================================

        if payment_amount <= 0:

            return {
                "success": False,
                "message": (
                    "Payment amount must be greater than zero."
                ),
            }


        # ========================================================
        # FIND CUSTOMER
        # ========================================================

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


        # ========================================================
        # RECORD KHATA PAYMENT
        # ========================================================

        payment = record_khata_payment(

            db=db,

            customer_id=customer.id,

            amount=payment_amount,

            note="Khata payment",

        )


        # ========================================================
        # SUCCESS RESPONSE
        # ========================================================

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


    except Exception as e:

        db.rollback()

        print(
            "Error recording Khata payment:",
            e
        )

        return {

            "success": False,

            "message": (
                "I couldn't record the Khata payment."
            ),

        }


    finally:

        db.close()