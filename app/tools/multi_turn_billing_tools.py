from decimal import Decimal

from app.database.connection import SessionLocal
from app.services.active_bill_service import (
    start_new_bill,
    add_product_to_active_bill,
    update_active_bill_item,
    remove_product_from_active_bill,
    get_active_bill_summary,
    set_active_bill_payment,
    finalize_active_bill,
    set_active_bill_customer,
)

def set_bill_customer_tool(customer_name):
    db = SessionLocal()

    try:
        return set_active_bill_customer(
            db=db,
            customer_name=customer_name,
        )

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()


def start_bill_tool() -> dict:

    db = SessionLocal()

    try:
        bill = start_new_bill(db)

        return {
            "success": True,
            "bill_id": bill.id,
            "message": (
                f"Started new draft bill #{bill.id}."
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


def add_to_current_bill_tool(
    product_name: str,
    quantity: float,
) -> dict:

    db = SessionLocal()

    try:
        result = add_product_to_active_bill(
            db=db,
            product_name=product_name,
            quantity=Decimal(str(quantity)),
        )

        return result

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()


def update_current_bill_item_tool(
    product_name: str,
    quantity: float,
) -> dict:

    db = SessionLocal()

    try:
        result = update_active_bill_item(
            db=db,
            product_name=product_name,
            quantity=Decimal(str(quantity)),
        )

        return result

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()


def remove_from_current_bill_tool(
    product_name: str,
) -> dict:

    db = SessionLocal()

    try:
        result = remove_product_from_active_bill(
            db=db,
            product_name=product_name,
        )

        return result

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()


def get_current_bill_tool() -> dict:

    db = SessionLocal()

    try:
        return get_active_bill_summary(db)

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()


def set_bill_payment_tool(
    payment_method: str,
) -> dict:

    db = SessionLocal()

    try:
        return set_active_bill_payment(
            db=db,
            payment_method=payment_method,
        )

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()


def finalize_current_bill_tool() -> dict:

    db = SessionLocal()

    try:
        return finalize_active_bill(db)

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()