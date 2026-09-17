from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.bill import Bill, BillStatus
from app.models.payment import Payment, PaymentMethod

from app.models.customer import Customer
from app.models.khata_entry import KhataEntry, KhataEntryType


def record_payment(
    db: Session,
    bill_id: int,
    amount: Decimal,
    method: PaymentMethod,
) -> Payment:

    # Amount must be positive
    if amount <= 0:
        raise ValueError(
            "Payment amount must be greater than zero."
        )

    # Find the bill
    bill = (
        db.query(Bill)
        .filter(Bill.id == bill_id)
        .first()
    )

    if bill is None:
        raise ValueError("Bill not found.")

    # Payment can only be recorded for finalized bills
    if bill.status != BillStatus.FINALIZED.value:
        raise ValueError(
            "Payment can only be recorded for a finalized bill."
        )

    # Get existing payments
    existing_payments = (
        db.query(Payment)
        .filter(Payment.bill_id == bill_id)
        .all()
    )

    already_paid = sum(
        (payment.amount for payment in existing_payments),
        Decimal("0.00")
    )

    remaining_amount = bill.total - already_paid

    # Bill is already fully paid
    if remaining_amount <= 0:
        raise ValueError(
            "Bill is already fully paid."
        )

    # Prevent overpayment
    if amount > remaining_amount:
        raise ValueError(
            f"Payment exceeds remaining amount. "
            f"Remaining: {remaining_amount}, "
            f"Attempted: {amount}"
        )

    # Create payment
    payment = Payment(
        bill_id=bill_id,
        amount=amount,
        method=method.value,
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment
def get_bill_outstanding(
    db: Session,
    bill_id: int,
) -> Decimal:

    bill = (
        db.query(Bill)
        .filter(Bill.id == bill_id)
        .first()
    )

    if bill is None:
        raise ValueError("Bill not found.")

    if bill.status != BillStatus.FINALIZED.value:
        raise ValueError(
            "Outstanding amount can only be checked for a finalized bill."
        )

    payments = (
        db.query(Payment)
        .filter(Payment.bill_id == bill_id)
        .all()
    )

    already_paid = sum(
        (payment.amount for payment in payments),
        Decimal("0.00"),
    )

    outstanding = bill.total - already_paid

    if outstanding < 0:
        outstanding = Decimal("0.00")

    return outstanding

def record_credit_payment(
    db: Session,
    customer_id: int,
    bill_id: int,
    amount: Decimal,
    method: PaymentMethod,
    note: str | None = None,
) -> tuple[Payment, KhataEntry]:

    try:
        if amount <= 0:
            raise ValueError(
                "Payment amount must be greater than zero."
            )

        if method == PaymentMethod.CREDIT:
            raise ValueError(
                "Credit is not a valid settlement method."
            )

        # Lock the customer while checking the Khata balance.
        customer = (
            db.query(Customer)
            .filter(Customer.id == customer_id)
            .with_for_update()
            .first()
        )

        if customer is None:
            raise ValueError("Customer not found.")

        if not customer.is_active:
            raise ValueError(
                "Cannot record payment for an inactive customer."
            )

        # Lock the bill.
        bill = (
            db.query(Bill)
            .filter(Bill.id == bill_id)
            .with_for_update()
            .first()
        )

        if bill is None:
            raise ValueError("Bill not found.")

        if bill.status != BillStatus.FINALIZED.value:
            raise ValueError(
                "Payment can only be recorded for a finalized bill."
            )

        if bill.customer_id != customer_id:
            raise ValueError(
                "Bill does not belong to this customer."
            )

        # Find existing payments for this bill.
        existing_payments = (
            db.query(Payment)
            .filter(Payment.bill_id == bill_id)
            .with_for_update()
            .all()
        )

        already_paid = sum(
            (payment.amount for payment in existing_payments),
            Decimal("0.00"),
        )

        remaining_bill_amount = bill.total - already_paid

        if remaining_bill_amount <= 0:
            raise ValueError(
                "This bill is already fully paid."
            )

        if amount > remaining_bill_amount:
            raise ValueError(
                f"Payment exceeds bill balance. "
                f"Remaining: {remaining_bill_amount}, "
                f"Attempted: {amount}"
            )

        # Calculate customer's Khata balance.
        khata_entries = (
            db.query(KhataEntry)
            .filter(
                KhataEntry.customer_id == customer_id
            )
            .with_for_update()
            .all()
        )

        current_balance = Decimal("0.00")

        for entry in khata_entries:

            if entry.entry_type == KhataEntryType.CREDIT.value:
                current_balance += entry.amount

            elif entry.entry_type == KhataEntryType.PAYMENT.value:
                current_balance -= entry.amount

        if current_balance <= 0:
            raise ValueError(
                "Customer has no outstanding Khata balance."
            )

        if amount > current_balance:
            raise ValueError(
                f"Payment exceeds customer balance. "
                f"Balance: {current_balance}, "
                f"Attempted: {amount}"
            )

        # Create actual payment record.
        payment = Payment(
            bill_id=bill_id,
            amount=amount,
            method=method.value,
        )

        db.add(payment)

        # Create Khata settlement record.
        khata_entry = KhataEntry(
            customer_id=customer_id,
            bill_id=bill_id,
            entry_type=KhataEntryType.PAYMENT.value,
            amount=amount,
            note=note,
        )

        db.add(khata_entry)

        # Both records are committed together.
        db.commit()

        db.refresh(payment)
        db.refresh(khata_entry)

        return payment, khata_entry

    except Exception:
        db.rollback()
        raise

