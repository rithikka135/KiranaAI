from decimal import Decimal

from app.database.connection import SessionLocal
from app.services.khata_service import add_credit


db = SessionLocal()

try:
    entry = add_credit(
        db=db,
        customer_id=1,
        amount=Decimal("500.00"),
        bill_id=None,
        note="Initial credit balance",
    )

    print("Credit added successfully!")
    print("Entry ID:", entry.id)
    print("Customer ID:", entry.customer_id)
    print("Type:", entry.entry_type)
    print("Amount:", entry.amount)
    print("Note:", entry.note)

finally:
    db.close()