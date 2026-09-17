from app.database.connection import SessionLocal
from app.models.bill import Bill
from app.models.inventory import Inventory
from app.models.khata_entry import KhataEntry


db = SessionLocal()

try:
    bill = (
        db.query(Bill)
        .order_by(Bill.id.desc())
        .first()
    )

    inventory = (
        db.query(Inventory)
        .filter(Inventory.product_id == 1)
        .first()
    )

    khata_entry = (
        db.query(KhataEntry)
        .filter(KhataEntry.bill_id == bill.id)
        .first()
    )

    print("Credit Sale Verification")
    print("-------------------------")

    print("Bill ID:", bill.id)
    print("Customer ID:", bill.customer_id)
    print("Status:", bill.status)
    print("Total:", bill.total)

    print("\nInventory")
    print("Rice stock:", inventory.quantity)

    print("\nKhata")
    print("Entry ID:", khata_entry.id)
    print("Entry type:", khata_entry.entry_type)
    print("Amount:", khata_entry.amount)
    print("Bill ID:", khata_entry.bill_id)

finally:
    db.close()