from app.database.connection import SessionLocal
from app.services.billing_service import create_bill


db = SessionLocal()

try:
    try:
        create_bill(
            db=db,
            payment_method="bitcoin",
        )

        print("ERROR: Invalid payment method was accepted.")

    except ValueError as e:
        print("Invalid payment method correctly rejected!")
        print("Reason:", e)

finally:
    db.close()