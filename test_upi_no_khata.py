from decimal import Decimal

from app.database.connection import SessionLocal
from app.services.billing_service import (
    create_bill,
    add_bill_item,
    finalize_bill,
)
from app.services.khata_service import get_customer_balance


db = SessionLocal()

try:
    before_balance = get_customer_balance(db, 1)

    print("Khata balance before:", before_balance)

    bill = create_bill(
        db=db,
        customer_id=1,
        payment_method="upi",
    )

    add_bill_item(
        db=db,
        bill_id=bill.id,
        product_id=1,
        quantity=Decimal("1"),
    )

    finalized_bill = finalize_bill(
        db=db,
        bill_id=bill.id,
    )

    after_balance = get_customer_balance(db, 1)

    print("Bill payment method:", finalized_bill.payment_method)
    print("Bill status:", finalized_bill.status)
    print("Khata balance after:", after_balance)

    if after_balance == before_balance:
        print("SUCCESS: UPI sale did not create a Khata entry.")
    else:
        print("ERROR: UPI sale incorrectly changed Khata balance.")

    raise RuntimeError("ROLLBACK TEST")

except RuntimeError as e:
    if str(e) == "ROLLBACK TEST":
        db.rollback()
        print("Test rolled back. Database unchanged.")
    else:
        raise

except Exception:
    db.rollback()
    raise

finally:
    db.close()