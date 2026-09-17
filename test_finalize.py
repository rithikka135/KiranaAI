from app.database.connection import SessionLocal
from app.services.billing_service import finalize_bill
from app.models.inventory import Inventory


db = SessionLocal()

try:
    # Check stock before finalization
    inventory_before = (
        db.query(Inventory)
        .filter(Inventory.product_id == 1)
        .first()
    )

    print("Stock before:", inventory_before.quantity)

    # Finalize Bill #1
    bill = finalize_bill(
        db=db,
        bill_id=1
    )

    print("\nBill finalized successfully!")
    print("Bill ID:", bill.id)
    print("Status:", bill.status)
    print("Subtotal:", bill.subtotal)
    print("CGST:", bill.cgst)
    print("SGST:", bill.sgst)
    print("Total Tax:", bill.total_tax)
    print("Total:", bill.total)

    # Check stock after finalization
    inventory_after = (
        db.query(Inventory)
        .filter(Inventory.product_id == 1)
        .first()
    )

    print("\nStock after:", inventory_after.quantity)

finally:
    db.close()