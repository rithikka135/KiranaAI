from decimal import Decimal

from app.database.connection import SessionLocal
from app.models.customer import Customer
from app.services.khata_service import (
    get_customer_balance,
    add_credit,
)


def check_customer_balance(
    customer_name: str,
) -> dict:

    db = SessionLocal()

    try:

        customer = (
            db.query(Customer)
            .filter(
                Customer.name.ilike(
                    f"%{customer_name}%"
                ),
                Customer.is_active == True,
            )
            .first()
        )

        if customer is None:
            return {
                "success": False,
                "message": (
                    f"Customer '{customer_name}' "
                    f"not found."
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
            "balance": str(balance),
            "message": (
                f"{customer.name} has an "
                f"outstanding balance of ₹{balance}."
            ),
        }

    except ValueError as e:

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()


def create_customer(
    customer_name: str,
) -> dict:

    db = SessionLocal()

    try:

        customer_name = customer_name.strip()

        if not customer_name:
            return {
                "success": False,
                "message": "Customer name cannot be empty.",
            }

        existing_customer = (
            db.query(Customer)
            .filter(
                Customer.name.ilike(customer_name),
                Customer.is_active == True,
            )
            .first()
        )

        if existing_customer is not None:
            return {
                "success": False,
                "message": (
                    f"Customer '{existing_customer.name}' "
                    "already exists."
                ),
            }

        customer = Customer(
            name=customer_name,
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)

        return {
            "success": True,
            "customer_id": customer.id,
            "customer_name": customer.name,
            "message": (
                f"Customer '{customer.name}' "
                "created successfully."
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

def add_customer_credit(
    customer_name: str,
    amount: str,
    note: str | None = None,
) -> dict:

    db = SessionLocal()

    try:

        customer_name = customer_name.strip()

        if not customer_name:
            return {
                "success": False,
                "message": "Customer name cannot be empty.",
            }

        customer = (
            db.query(Customer)
            .filter(
                Customer.name.ilike(customer_name),
                Customer.is_active == True,
            )
            .first()
        )

        if customer is None:
            return {
                "success": False,
                "message": (
                    f"Customer '{customer_name}' "
                    "not found."
                ),
            }

        credit_amount = Decimal(str(amount))

        if credit_amount <= 0:
            return {
                "success": False,
                "message": (
                    "Credit amount must be greater than zero."
                ),
            }

        entry = add_credit(
            db=db,
            customer_id=customer.id,
            amount=credit_amount,
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
            "credit_amount": str(entry.amount),
            "balance": str(balance),
            "message": (
                f"₹{entry.amount} credit added to "
                f"{customer.name}'s Khata. "
                f"Outstanding balance: ₹{balance}."
            ),
        }

    except ValueError as e:

        db.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    except Exception as e:

        db.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()