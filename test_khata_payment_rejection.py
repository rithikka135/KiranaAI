from decimal import Decimal

from app.database.connection import SessionLocal
from app.services.khata_service import (
    get_customer_balance,
    record_khata_payment,
)

db = SessionLocal()

try:
    balance_before = get_customer_balance(
        db=db,
        customer_id=1,
    )

    print("Balance before:", balance_before)

    try:
        record_khata_payment(
            db=db,
            customer_id=1,
            amount=Decimal("10000.00"),
            note="Invalid test payment",
        )

        print("ERROR: Payment should have been rejected.")

    except ValueError as e:
        print("Payment correctly rejected!")
        print("Reason:", e)

    balance_after = get_customer_balance(
        db=db,
        customer_id=1,
    )

    print("Balance after:", balance_after)

finally:
    db.close()