from app.database.connection import SessionLocal
from app.services.billing_service import get_bill


db = SessionLocal()

try:
    bill, items = get_bill(
        db=db,
        bill_id=1
    )

    print("Bill ID:", bill.id)
    print("Status:", bill.status)
    print("Subtotal:", bill.subtotal)
    print("CGST:", bill.cgst)
    print("SGST:", bill.sgst)
    print("Total Tax:", bill.total_tax)
    print("Total:", bill.total)

    print("\nItems:")

    for item in items:
        print(
            f"Item ID: {item.id}, "
            f"Product ID: {item.product_id}, "
            f"Quantity: {item.quantity}, "
            f"Unit Price: {item.unit_price}, "
            f"Total: {item.total_amount}"
        )

finally:
    db.close()