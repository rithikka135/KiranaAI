from decimal import Decimal

from app.database.connection import SessionLocal
from app.models.bill import Bill
from app.models.bill_item import BillItem
from app.models.inventory import Inventory
from app.models.payment import Payment
from app.models.khata_entry import KhataEntry


db = SessionLocal()

try:
    bill_id = 5

    bill = (
        db.query(Bill)
        .filter(Bill.id == bill_id)
        .first()
    )

    if bill is None:
        raise ValueError("Bill #5 not found.")

    print("Deleting Bill #5...")

    # Find bill items
    items = (
        db.query(BillItem)
        .filter(BillItem.bill_id == bill_id)
        .all()
    )

    # Restore inventory
    for item in items:
        inventory = (
            db.query(Inventory)
            .filter(Inventory.product_id == item.product_id)
            .first()
        )

        if inventory is not None:
            inventory.quantity += item.quantity
            print(
                f"Restored {item.quantity} "
                f"units of product {item.product_id}"
            )

    # Delete any payments for this temporary bill
    db.query(Payment).filter(
        Payment.bill_id == bill_id
    ).delete()

    # Delete any Khata entries for this temporary bill
    db.query(KhataEntry).filter(
        KhataEntry.bill_id == bill_id
    ).delete()

    # Delete bill items
    db.query(BillItem).filter(
        BillItem.bill_id == bill_id
    ).delete()

    # Delete bill
    db.delete(bill)

    db.commit()

    print("Bill #5 cleaned up successfully.")

finally:
    db.close()