from app.database.connection import SessionLocal
from app.services.billing_service import create_bill


db = SessionLocal()

try:
    try:
        bill = create_bill(
            db=db,
            customer_id=None,
            payment_method="credit",
        )

        print("ERROR: Credit sale should have been rejected.")

        db.delete(bill)
        db.commit()

    except ValueError as e:
        print("Credit sale correctly rejected!")
        print("Reason:", e)

finally:
    db.close()