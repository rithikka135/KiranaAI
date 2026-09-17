from decimal import Decimal

from app.database.connection import SessionLocal
from app.services.billing_service import (
    create_bill,
    add_bill_item,
    finalize_bill,
)
from app.services.khata_service import get_customer_balance


db = SessionLocal()

try:
    # Create a new draft bill for Ravi.
    bill = create_bill(
    db=db,
    customer_id=1,
    payment_method="credit",
)

    print("Draft bill created!")
    print("Bill ID:", bill.id)

    # Add 2 kg of rice.
    add_bill_item(
        db=db,
        bill_id=bill.id,
        product_id=1,
        quantity=Decimal("2.000"),
    )

    print("Item added.")

    # Finalize the credit sale.
    finalized_bill = finalize_bill(
        db=db,
        bill_id=bill.id,
    )

    print("Credit sale finalized!")
    print("Bill ID:", finalized_bill.id)
    print("Customer ID:", finalized_bill.customer_id)
    print("Total:", finalized_bill.total)

    # Check Ravi's new Khata balance.
    balance = get_customer_balance(
        db=db,
        customer_id=1,
    )

    print("Ravi's new Khata balance: ₹", balance)

finally:
    db.close()