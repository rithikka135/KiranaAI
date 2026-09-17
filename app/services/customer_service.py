from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.khata import Khata


def create_customer(
    db: Session,
    name: str,
    phone: str | None = None,
):
    name = name.strip()

    if not name:
        raise ValueError("Customer name is required.")

    if phone:
        phone = phone.strip()

    # Avoid duplicate phone numbers when phone is provided.
    if phone:
        existing = (
            db.query(Customer)
            .filter(Customer.phone == phone)
            .first()
        )

        if existing:
            raise ValueError(
                f"Customer with phone {phone} already exists."
            )

    customer = Customer(
        name=name,
        phone=phone,
    )

    db.add(customer)
    db.flush()

    # Every customer gets a Khata account.
    khata = Khata(
        customer_id=customer.id,
        balance=Decimal("0.00"),
    )

    db.add(khata)
    db.commit()

    db.refresh(customer)

    return customer


def find_customer(
    db: Session,
    name: str,
):
    name = name.strip()

    if not name:
        return None

    return (
        db.query(Customer)
        .filter(Customer.name.ilike(f"%{name}%"))
        .first()
    )


def get_customer(
    db: Session,
    customer_id: int,
):
    return (
        db.query(Customer)
        .filter(Customer.id == customer_id)
        .first()
    )


def get_customer_balance(
    db: Session,
    customer_id: int,
):
    customer = get_customer(db, customer_id)

    if customer is None:
        raise ValueError("Customer not found.")

    khata = (
        db.query(Khata)
        .filter(Khata.customer_id == customer_id)
        .first()
    )

    if khata is None:
        raise ValueError(
            f"Khata account does not exist for {customer.name}."
        )

    return {
        "customer_id": customer.id,
        "customer_name": customer.name,
        "phone": customer.phone,
        "balance": str(khata.balance),
    }