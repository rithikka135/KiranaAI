from app.database.connection import SessionLocal
from app.services.payment_service import get_bill_outstanding


db = SessionLocal()

try:
    outstanding = get_bill_outstanding(
        db=db,
        bill_id=2,
    )

    print("Bill #2 outstanding amount:", outstanding)

finally:
    db.close()