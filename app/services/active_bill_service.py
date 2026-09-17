from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.active_bill_session import ActiveBillSession
from app.models.bill import Bill, BillStatus
from app.models.bill_item import BillItem
from app.models.product import Product
from app.models.customer import Customer

from app.services.billing_service import (
    create_bill,
    add_bill_item,
    calculate_bill,
    update_bill_item,
    remove_bill_item,
    get_bill,
    finalize_bill,
)


DEFAULT_SESSION_KEY = "default_owner"


def get_active_session(
    db: Session,
    session_key: str = DEFAULT_SESSION_KEY,
) -> ActiveBillSession | None:

    return (
        db.query(ActiveBillSession)
        .filter(
            ActiveBillSession.session_key == session_key
        )
        .first()
    )


def get_active_bill(
    db: Session,
    session_key: str = DEFAULT_SESSION_KEY,
) -> Bill | None:

    session = get_active_session(
        db,
        session_key,
    )

    if session is None:
        return None

    bill = (
        db.query(Bill)
        .filter(Bill.id == session.bill_id)
        .first()
    )

    if bill is None:
        return None

    if bill.status != BillStatus.DRAFT.value:
        return None

    return bill


def start_new_bill(
    db: Session,
    session_key: str = DEFAULT_SESSION_KEY,
) -> Bill:

    existing = get_active_bill(
        db,
        session_key,
    )

    if existing is not None:
        raise ValueError(
            f"Bill #{existing.id} is already open. "
            "Add items to the current bill or finalize it first."
        )

    old_session = get_active_session(
        db,
        session_key,
    )

    if old_session is not None:
        db.delete(old_session)
        db.commit()

    bill = create_bill(
        db=db,
        customer_id=None,
        payment_method=None,
    )

    session = ActiveBillSession(
        session_key=session_key,
        bill_id=bill.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(session)
    db.commit()

    return bill


def add_product_to_active_bill(
    db: Session,
    product_name: str,
    quantity: Decimal,
    session_key: str = DEFAULT_SESSION_KEY,
) -> dict:

    if quantity <= 0:
        raise ValueError(
            "Quantity must be greater than zero."
        )

    bill = get_active_bill(
        db,
        session_key,
    )

    if bill is None:
        raise ValueError(
            "There is no active bill. "
            "Start a bill first."
        )

    product = (
        db.query(Product)
        .filter(
            Product.name.ilike(
                f"%{product_name}%"
            ),
            Product.is_active == True,
        )
        .first()
    )

    if product is None:
        raise ValueError(
            f"Product '{product_name}' not found."
        )

    existing_item = (
        db.query(BillItem)
        .filter(
            BillItem.bill_id == bill.id,
            BillItem.product_id == product.id,
        )
        .first()
    )

    if existing_item is not None:

        new_quantity = (
            existing_item.quantity + quantity
        )

        item = update_bill_item(
            db=db,
            bill_item_id=existing_item.id,
            quantity=new_quantity,
        )

    else:

        item = add_bill_item(
            db=db,
            bill_id=bill.id,
            product_id=product.id,
            quantity=quantity,
        )

    calculate_bill(
        db=db,
        bill_id=bill.id,
    )

    session = get_active_session(
        db,
        session_key,
    )

    if session is not None:
        session.updated_at = datetime.utcnow()
        db.commit()

    return {
        "success": True,
        "bill_id": bill.id,
        "item_id": item.id,
        "product_name": product.name,
        "quantity": str(item.quantity),
        "unit": product.unit,
        "unit_price": str(item.unit_price),
        "gst_rate": str(item.gst_rate),
        "hsn_code": item.hsn_code,
        "subtotal": str(bill.subtotal),
        "cgst": str(bill.cgst),
        "sgst": str(bill.sgst),
        "total": str(bill.total),
    }


def update_active_bill_item(
    db: Session,
    product_name: str,
    quantity: Decimal,
    session_key: str = DEFAULT_SESSION_KEY,
) -> dict:

    if quantity <= 0:
        raise ValueError(
            "Quantity must be greater than zero."
        )

    bill = get_active_bill(
        db,
        session_key,
    )

    if bill is None:
        raise ValueError(
            "There is no active bill."
        )

    product = (
        db.query(Product)
        .filter(
            Product.name.ilike(
                f"%{product_name}%"
            ),
            Product.is_active == True,
        )
        .first()
    )

    if product is None:
        raise ValueError(
            f"Product '{product_name}' not found."
        )

    item = (
        db.query(BillItem)
        .filter(
            BillItem.bill_id == bill.id,
            BillItem.product_id == product.id,
        )
        .first()
    )

    if item is None:
        raise ValueError(
            f"{product.name} is not in the current bill."
        )

    update_bill_item(
        db=db,
        bill_item_id=item.id,
        quantity=quantity,
    )

    calculate_bill(
        db=db,
        bill_id=bill.id,
    )

    return {
        "success": True,
        "bill_id": bill.id,
        "product_name": product.name,
        "quantity": str(quantity),
        "unit": product.unit,
        "subtotal": str(bill.subtotal),
        "cgst": str(bill.cgst),
        "sgst": str(bill.sgst),
        "total": str(bill.total),
    }


def remove_product_from_active_bill(
    db: Session,
    product_name: str,
    session_key: str = DEFAULT_SESSION_KEY,
) -> dict:

    bill = get_active_bill(
        db,
        session_key,
    )

    if bill is None:
        raise ValueError(
            "There is no active bill."
        )

    product = (
        db.query(Product)
        .filter(
            Product.name.ilike(
                f"%{product_name}%"
            ),
            Product.is_active == True,
        )
        .first()
    )

    if product is None:
        raise ValueError(
            f"Product '{product_name}' not found."
        )

    item = (
        db.query(BillItem)
        .filter(
            BillItem.bill_id == bill.id,
            BillItem.product_id == product.id,
        )
        .first()
    )

    if item is None:
        raise ValueError(
            f"{product.name} is not in the current bill."
        )

    remove_bill_item(
        db=db,
        bill_item_id=item.id,
    )

    calculate_bill(
        db=db,
        bill_id=bill.id,
    )

    return {
        "success": True,
        "bill_id": bill.id,
        "product_name": product.name,
        "subtotal": str(bill.subtotal),
        "cgst": str(bill.cgst),
        "sgst": str(bill.sgst),
        "total": str(bill.total),
    }


def get_active_bill_summary(
    db: Session,
    session_key: str = DEFAULT_SESSION_KEY,
) -> dict:

    bill = get_active_bill(
        db,
        session_key,
    )

    if bill is None:
        return {
            "success": False,
            "message": "There is no active bill.",
        }

    bill, items = get_bill(
        db,
        bill.id,
    )

    item_details = []

    for item in items:

        product = (
            db.query(Product)
            .filter(Product.id == item.product_id)
            .first()
        )

        item_details.append(
            {
                "item_id": item.id,
                "product_id": item.product_id,
                "product_name": (
                    product.name
                    if product
                    else "Unknown Product"
                ),
                "quantity": str(item.quantity),
                "unit": (
                    product.unit
                    if product
                    else ""
                ),
                "unit_price": str(item.unit_price),
                "gst_rate": str(item.gst_rate),
                "hsn_code": item.hsn_code,
                "taxable_amount": str(
                    item.taxable_amount
                ),
                "cgst": str(item.cgst),
                "sgst": str(item.sgst),
                "total_amount": str(
                    item.total_amount
                ),
            }
        )

    customer_name = None
    customer_phone = None

    if bill.customer_id is not None:

        customer = (
            db.query(Customer)
            .filter(Customer.id == bill.customer_id)
            .first()
        )

        if customer is not None:
            customer_name = customer.name
            customer_phone = customer.phone

    return {
        "success": True,
        "bill_id": bill.id,
        "status": bill.status,
        "payment_method": bill.payment_method,
        "customer_id": bill.customer_id,
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "items": item_details,
        "subtotal": str(bill.subtotal),
        "cgst": str(bill.cgst),
        "sgst": str(bill.sgst),
        "total_tax": str(bill.total_tax),
        "total": str(bill.total),
    }


def set_active_bill_payment(
    db: Session,
    payment_method: str,
    session_key: str = DEFAULT_SESSION_KEY,
) -> dict:

    allowed_methods = {
        "cash",
        "upi",
        "card",
        "credit",
    }

    payment_method = (
        payment_method.lower().strip()
    )

    if payment_method not in allowed_methods:
        raise ValueError(
            "Payment method must be cash, UPI, card, or credit."
        )

    bill = get_active_bill(
        db,
        session_key,
    )

    if bill is None:
        raise ValueError(
            "There is no active bill."
        )

    # Credit is allowed only when a customer
    # has been attached to the bill.
    if payment_method == "credit":

        if bill.customer_id is None:
            raise ValueError(
                "Credit payment requires a customer. "
                "Please attach a customer to the bill first."
            )

        customer = (
            db.query(Customer)
            .filter(
                Customer.id == bill.customer_id,
                Customer.is_active == True,
            )
            .first()
        )

        if customer is None:
            raise ValueError(
                "The selected customer was not found "
                "or is inactive."
            )

    bill.payment_method = payment_method

    db.commit()
    db.refresh(bill)

    return {
        "success": True,
        "bill_id": bill.id,
        "payment_method": bill.payment_method,
        "customer_id": bill.customer_id,
        "total": str(bill.total),
    }


def finalize_active_bill(
    db: Session,
    session_key: str = DEFAULT_SESSION_KEY,
) -> dict:

    bill = get_active_bill(
        db,
        session_key,
    )

    if bill is None:
        raise ValueError(
            "There is no active bill."
        )

    if not bill.payment_method:
        raise ValueError(
            "Please choose a payment method "
            "before finalizing the bill: "
            "cash, UPI, card, or credit."
        )

    if (
        bill.payment_method == "credit"
        and bill.customer_id is None
    ):
        raise ValueError(
            "Credit payment requires a customer. "
            "Please attach a customer to the bill first."
        )

    bill_id = bill.id

    finalized_bill = finalize_bill(
        db=db,
        bill_id=bill_id,
    )

    session = get_active_session(
        db,
        session_key,
    )

    if session is not None:
        db.delete(session)
        db.commit()

    return {
        "success": True,
        "bill_id": finalized_bill.id,
        "status": finalized_bill.status,
        "payment_method": finalized_bill.payment_method,
        "customer_id": finalized_bill.customer_id,
        "subtotal": str(
            finalized_bill.subtotal
        ),
        "cgst": str(
            finalized_bill.cgst
        ),
        "sgst": str(
            finalized_bill.sgst
        ),
        "total_tax": str(
            finalized_bill.total_tax
        ),
        "total": str(
            finalized_bill.total
        ),
    }


def set_active_bill_customer(
    db: Session,
    customer_name: str,
    session_key: str = DEFAULT_SESSION_KEY,
) -> dict:

    bill = get_active_bill(
        db,
        session_key,
    )

    if bill is None:
        raise ValueError(
            "There is no active bill. Start a bill first."
        )

    customer_name = customer_name.strip()

    if not customer_name:
        raise ValueError(
            "Customer name is required."
        )

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
        raise ValueError(
            f"Customer '{customer_name}' was not found."
        )

    bill.customer_id = customer.id

    db.commit()
    db.refresh(bill)

    return {
        "success": True,
        "bill_id": bill.id,
        "customer_id": customer.id,
        "customer_name": customer.name,
        "phone": customer.phone,
    }