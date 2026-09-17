from app.database.connection import SessionLocal
from app.services.khata_service import get_customer_balance


db = SessionLocal()

try:
    balance = get_customer_balance(
        db=db,
        customer_id=1,
    )

    print("Khata balance calculated successfully!")
    print("Customer ID:", 1)
    print("Amount owed: ₹", balance)

finally:
    db.close()