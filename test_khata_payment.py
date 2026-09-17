from decimal import Decimal

from app.database.connection import SessionLocal
from app.services.khata_service import (
    record_khata_payment,
    get_customer_balance,
)


db = SessionLocal()

try:
    payment = record_khata_payment(
        db=db,
        customer_id=1,
        amount=Decimal("200.00"),
        note="Cash payment",
    )

    print("Khata payment recorded successfully!")
    print("Entry ID:", payment.id)
    print("Customer ID:", payment.customer_id)
    print("Type:", payment.entry_type)
    print("Amount:", payment.amount)
    print("Note:", payment.note)

    balance = get_customer_balance(
        db=db,
        customer_id=1,
    )

    print("Remaining balance: ₹", balance)

finally:
    db.close()