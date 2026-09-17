from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.khata_entry import KhataEntry, KhataEntryType


def create_customer(
    db: Session,
    name: str,
    phone: str | None = None,
) -> Customer:

    name = name.strip()

    if not name:
        raise ValueError("Customer name cannot be empty.")

    customer = Customer(
        name=name,
        phone=phone,
        is_active=True,
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


def add_credit(
    db: Session,
    customer_id: int,
    amount: Decimal,
    bill_id: int | None = None,
    note: str | None = None,
) -> KhataEntry:

    if amount <= 0:
        raise ValueError(
            "Credit amount must be greater than zero."
        )

    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id)
        .first()
    )

    if customer is None:
        raise ValueError("Customer not found.")

    if not customer.is_active:
        raise ValueError(
            "Cannot add credit for an inactive customer."
        )

    entry = KhataEntry(
        customer_id=customer_id,
        bill_id=bill_id,
        entry_type=KhataEntryType.CREDIT.value,
        amount=amount,
        note=note,
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    return entry

def get_customer_balance(
    db: Session,
    customer_id: int,
) -> Decimal:

    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id)
        .first()
    )

    if customer is None:
        raise ValueError("Customer not found.")

    entries = (
        db.query(KhataEntry)
        .filter(KhataEntry.customer_id == customer_id)
        .all()
    )

    balance = Decimal("0.00")

    for entry in entries:

        if entry.entry_type == KhataEntryType.CREDIT.value:
            balance += entry.amount

        elif entry.entry_type == KhataEntryType.PAYMENT.value:
            balance -= entry.amount

    return balance

def record_khata_payment(
    db: Session,
    customer_id: int,
    amount: Decimal,
    bill_id: int | None = None,
    note: str | None = None,
) -> KhataEntry:

    try:
        if amount <= 0:
            raise ValueError(
                "Payment amount must be greater than zero."
            )

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

        entries = (
            db.query(KhataEntry)
            .filter(KhataEntry.customer_id == customer_id)
            .with_for_update()
            .all()
        )

        current_balance = Decimal("0.00")

        for entry in entries:

            if entry.entry_type == KhataEntryType.CREDIT.value:
                current_balance += entry.amount

            elif entry.entry_type == KhataEntryType.PAYMENT.value:
                current_balance -= entry.amount

        if current_balance <= 0:
            raise ValueError(
                "Customer has no outstanding balance."
            )

        if amount > current_balance:
            raise ValueError(
                f"Payment exceeds outstanding balance. "
                f"Balance: {current_balance}, "
                f"Attempted: {amount}"
            )

        entry = KhataEntry(
            customer_id=customer_id,
            bill_id=bill_id,
            entry_type=KhataEntryType.PAYMENT.value,
            amount=amount,
            note=note,
        )

        db.add(entry)
        db.commit()
        db.refresh(entry)

        return entry

    except Exception:
        db.rollback()
        raise