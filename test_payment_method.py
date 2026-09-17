from app.database.connection import SessionLocal
from app.services.billing_service import create_bill


db = SessionLocal()

try:
    bill = create_bill(
        db=db,
        customer_id=1,
        payment_method="credit",
    )

    print("Draft bill created successfully!")
    print("Bill ID:", bill.id)
    print("Customer ID:", bill.customer_id)
    print("Payment method:", bill.payment_method)
    print("Status:", bill.status)

    # Delete the temporary draft bill.
    db.delete(bill)
    db.commit()

    print("\nTemporary draft bill deleted.")

finally:
    db.close()