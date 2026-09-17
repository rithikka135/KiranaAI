from decimal import Decimal

from app.database.connection import SessionLocal
from app.models.payment import PaymentMethod
from app.services.payment_service import record_payment


db = SessionLocal()

try:
    payment = record_payment(
        db=db,
        bill_id=1,
        amount=Decimal("157.50"),
        method=PaymentMethod.UPI,
    )

    print("Payment recorded successfully!")
    print("Payment ID:", payment.id)
    print("Bill ID:", payment.bill_id)
    print("Amount:", payment.amount)
    print("Method:", payment.method)

finally:
    db.close()