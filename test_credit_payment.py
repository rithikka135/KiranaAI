from decimal import Decimal

from app.database.connection import SessionLocal
from app.services.payment_service import record_credit_payment
from app.services.khata_service import get_customer_balance
from app.models.payment import PaymentMethod


db = SessionLocal()

try:
    balance_before = get_customer_balance(
        db=db,
        customer_id=1,
    )

    print("Balance before:", balance_before)

    payment, khata_entry = record_credit_payment(
        db=db,
        customer_id=1,
        bill_id=2,
        amount=Decimal("100.00"),
        method=PaymentMethod.UPI,
        note="₹100 UPI payment against Bill #2",
    )

    print("\nCredit payment recorded successfully!")

    print("\nPayment")
    print("Payment ID:", payment.id)
    print("Bill ID:", payment.bill_id)
    print("Amount:", payment.amount)
    print("Method:", payment.method)

    print("\nKhata Entry")
    print("Entry ID:", khata_entry.id)
    print("Customer ID:", khata_entry.customer_id)
    print("Bill ID:", khata_entry.bill_id)
    print("Entry type:", khata_entry.entry_type)
    print("Amount:", khata_entry.amount)

    balance_after = get_customer_balance(
        db=db,
        customer_id=1,
    )

    print("\nBalance after:", balance_after)

finally:
    db.close()