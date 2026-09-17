from app.database.connection import SessionLocal
from app.services.khata_service import create_customer


db = SessionLocal()

try:
    customer = create_customer(
        db=db,
        name="Ravi",
        phone="9876543210",
    )

    print("Customer created successfully!")
    print("Customer ID:", customer.id)
    print("Name:", customer.name)
    print("Phone:", customer.phone)
    print("Active:", customer.is_active)

finally:
    db.close()