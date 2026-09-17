from decimal import Decimal

from app.database.connection import SessionLocal
from app.models.customer import Customer
from app.services.khata_service import (
    create_customer,
    get_customer_balance,
    record_khata_payment,
)


def create_customer_tool(
    name: str,
    phone: str | None = None,
):
    db = SessionLocal()

    try:
        # Check for an existing active customer with the same phone.
        if phone:
            existing = (
                db.query(Customer)
                .filter(
                    Customer.phone == phone,
                    Customer.is_active == True,
                )
                .first()
            )

            if existing:
                return {
                    "success": False,
                    "message": (
                        f"Customer with phone {phone} "
                        f"already exists: {existing.name}."
                    ),
                }

        customer = create_customer(
            db=db,
            name=name,
            phone=phone,
        )

        return {
            "success": True,
            "customer_id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
            "message": (
                f"Customer '{customer.name}' "
                f"created successfully."
            ),
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()


def find_customer_tool(
    name: str,
):
    db = SessionLocal()

    try:
        customer = (
            db.query(Customer)
            .filter(
                Customer.name.ilike(f"%{name.strip()}%"),
                Customer.is_active == True,
            )
            .first()
        )

        if customer is None:
            return {
                "success": False,
                "message": (
                    f"Customer '{name}' was not found."
                ),
            }

        balance = get_customer_balance(
            db=db,
            customer_id=customer.id,
        )

        return {
            "success": True,
            "customer_id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
            "balance": str(balance),
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()


def customer_balance_tool(
    name: str,
):
    db = SessionLocal()

    try:
        customer = (
            db.query(Customer)
            .filter(
                Customer.name.ilike(f"%{name.strip()}%"),
                Customer.is_active == True,
            )
            .first()
        )

        if customer is None:
            return {
                "success": False,
                "message": (
                    f"Customer '{name}' was not found."
                ),
            }

        balance = get_customer_balance(
            db=db,
            customer_id=customer.id,
        )

        return {
            "success": True,
            "customer_id": customer.id,
            "customer_name": customer.name,
            "phone": customer.phone,
            "balance": str(balance),
            "message": (
                f"{customer.name} owes ₹{balance}."
            ),
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()


def record_customer_payment_tool(
    name: str,
    amount,
    note: str | None = None,
):
    db = SessionLocal()

    try:
        customer = (
            db.query(Customer)
            .filter(
                Customer.name.ilike(f"%{name.strip()}%"),
                Customer.is_active == True,
            )
            .first()
        )

        if customer is None:
            return {
                "success": False,
                "message": (
                    f"Customer '{name}' was not found."
                ),
            }

        payment = record_khata_payment(
            db=db,
            customer_id=customer.id,
            amount=Decimal(str(amount)),
            note=note,
        )

        balance = get_customer_balance(
            db=db,
            customer_id=customer.id,
        )

        return {
            "success": True,
            "customer_id": customer.id,
            "customer_name": customer.name,
            "payment": str(payment.amount),
            "balance": str(balance),
            "message": (
                f"₹{payment.amount} payment recorded for "
                f"{customer.name}. "
                f"Remaining balance: ₹{balance}."
            ),
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()