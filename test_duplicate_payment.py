from decimal import Decimal

from app.database.connection import SessionLocal
from app.models.payment import PaymentMethod
from app.services.payment_service import record_payment


db = SessionLocal()

try:
    try:
        record_payment(
            db=db,
            bill_id=1,
            amount=Decimal("10.00"),
            method=PaymentMethod.CASH,
        )

        print("ERROR: Duplicate payment was accepted!")

    except ValueError as e:
        print("Payment correctly rejected!")
        print("Reason:", e)

finally:
    db.close()