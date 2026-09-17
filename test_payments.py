from app.database.connection import SessionLocal
from app.models.payment import Payment


db = SessionLocal()

try:

    payments = (
        db.query(Payment)
        .order_by(Payment.id)
        .all()
    )

    print("\nKiranaAI Payments:")
    print("------------------")

    for payment in payments:
        print(
            f"Payment ID: {payment.id} | "
            f"Bill ID: {payment.bill_id} | "
            f"Amount: ₹{payment.amount} | "
            f"Method: {payment.method}"
        )

finally:
    db.close()