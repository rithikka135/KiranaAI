from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from app.models.khata_entry import KhataEntry, KhataEntryType
from app.models.customer import Customer

from app.models.bill import Bill, BillStatus
from app.models.bill_item import BillItem
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.payment import Payment, PaymentMethod


def create_bill(
    db: Session,
    customer_id: int | None = None,
    payment_method: str | None = None,
) -> Bill:

    allowed_methods = {
        PaymentMethod.CASH.value,
        PaymentMethod.UPI.value,
        PaymentMethod.CARD.value,
        PaymentMethod.CREDIT.value,
    }

    if payment_method is not None and payment_method not in allowed_methods:
        raise ValueError(
            f"Invalid payment method: {payment_method}"
        )

    if payment_method == "credit" and customer_id is None:
        raise ValueError(
            "Credit sale requires a customer."
        )

    if customer_id is not None:

        customer = (
            db.query(Customer)
            .filter(Customer.id == customer_id)
            .first()
        )

        if customer is None:
            raise ValueError("Customer not found.")

        if not customer.is_active:
            raise ValueError(
                "Cannot create a bill for an inactive customer."
            )

    bill = Bill(
        customer_id=customer_id,
        payment_method=payment_method,
        status=BillStatus.DRAFT.value,
        subtotal=Decimal("0.00"),
        cgst=Decimal("0.00"),
        sgst=Decimal("0.00"),
        total_tax=Decimal("0.00"),
        total=Decimal("0.00"),
    )

    db.add(bill)
    db.commit()
    db.refresh(bill)

    return bill


def add_bill_item(
    db: Session,
    bill_id: int,
    product_id: int,
    quantity: Decimal,
) -> BillItem:

    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")

    # Find the bill
    bill = (
        db.query(Bill)
        .filter(Bill.id == bill_id)
        .first()
    )

    if bill is None:
        raise ValueError("Bill not found.")

    # Only draft bills can be modified
    if bill.status != BillStatus.DRAFT.value:
        raise ValueError("Only draft bills can be modified.")

    # Find the product
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if product is None:
        raise ValueError("Product not found.")

    if not product.is_active:
        raise ValueError("Product is inactive.")

    # Calculate the amount
    taxable_amount = (
        product.selling_price * quantity
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    # GST percentage
    gst_amount = (
        taxable_amount * product.gst_rate / Decimal("100")
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    cgst = (
        gst_amount / Decimal("2")
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    sgst = gst_amount - cgst

    total_amount = taxable_amount + gst_amount

    # Create bill item
    bill_item = BillItem(
        bill_id=bill_id,
        product_id=product_id,
        quantity=quantity,
        unit_price=product.selling_price,
        gst_rate=product.gst_rate,
        hsn_code=product.hsn_code,
        taxable_amount=taxable_amount,
        cgst=cgst,
        sgst=sgst,
        total_amount=total_amount,
    )

    db.add(bill_item)
    db.commit()
    db.refresh(bill_item)

    return bill_item


def calculate_bill(
    db: Session,
    bill_id: int,
) -> Bill:

    # Find the bill
    bill = (
        db.query(Bill)
        .filter(Bill.id == bill_id)
        .first()
    )

    if bill is None:
        raise ValueError("Bill not found.")

    # Only draft bills can be calculated/modified
    if bill.status != BillStatus.DRAFT.value:
        raise ValueError("Only draft bills can be calculated.")

    # Get all items in this bill
    items = (
        db.query(BillItem)
        .filter(BillItem.bill_id == bill_id)
        .all()
    )

    # Start from zero
    subtotal = Decimal("0.00")
    cgst = Decimal("0.00")
    sgst = Decimal("0.00")

    # Add each item's values
    for item in items:
        subtotal += item.taxable_amount
        cgst += item.cgst
        sgst += item.sgst

    total_tax = cgst + sgst
    total = subtotal + total_tax

    # Update the bill
    bill.subtotal = subtotal
    bill.cgst = cgst
    bill.sgst = sgst
    bill.total_tax = total_tax
    bill.total = total

    db.commit()
    db.refresh(bill)

    return bill


def update_bill_item(
    db: Session,
    bill_item_id: int,
    quantity: Decimal,
) -> BillItem:

    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")

    # Find the bill item
    item = (
        db.query(BillItem)
        .filter(BillItem.id == bill_item_id)
        .first()
    )

    if item is None:
        raise ValueError("Bill item not found.")

    # Find the bill
    bill = (
        db.query(Bill)
        .filter(Bill.id == item.bill_id)
        .first()
    )

    if bill is None:
        raise ValueError("Bill not found.")

    # Only draft bills can be modified
    if bill.status != BillStatus.DRAFT.value:
        raise ValueError("Only draft bills can be modified.")

    # Recalculate using the price/GST
    # already captured in this bill item
    taxable_amount = (
        item.unit_price * quantity
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    gst_amount = (
        taxable_amount * item.gst_rate / Decimal("100")
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    cgst = (
        gst_amount / Decimal("2")
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    sgst = gst_amount - cgst

    total_amount = taxable_amount + gst_amount

    # Update the item
    item.quantity = quantity
    item.taxable_amount = taxable_amount
    item.cgst = cgst
    item.sgst = sgst
    item.total_amount = total_amount

    db.commit()
    db.refresh(item)

    return item


def remove_bill_item(
    db: Session,
    bill_item_id: int,
) -> None:

    # Find the bill item
    item = (
        db.query(BillItem)
        .filter(BillItem.id == bill_item_id)
        .first()
    )

    if item is None:
        raise ValueError("Bill item not found.")

    # Find the bill
    bill = (
        db.query(Bill)
        .filter(Bill.id == item.bill_id)
        .first()
    )

    if bill is None:
        raise ValueError("Bill not found.")

    # Only draft bills can be modified
    if bill.status != BillStatus.DRAFT.value:
        raise ValueError("Only draft bills can be modified.")

    db.delete(item)
    db.commit()


def get_bill(
    db: Session,
    bill_id: int,
) -> tuple[Bill, list[BillItem]]:

    # Find the bill
    bill = (
        db.query(Bill)
        .filter(Bill.id == bill_id)
        .first()
    )

    if bill is None:
        raise ValueError("Bill not found.")

    # Get all items belonging to this bill
    items = (
        db.query(BillItem)
        .filter(BillItem.bill_id == bill_id)
        .all()
    )

    return bill, items


def finalize_bill(
    db: Session,
    bill_id: int,
) -> Bill:

    try:
        bill = (
            db.query(Bill)
            .filter(Bill.id == bill_id)
            .first()
        )

        if bill is None:
            raise ValueError("Bill not found.")

        if bill.status != BillStatus.DRAFT.value:
            raise ValueError("Only draft bills can be finalized.")

        items = (
            db.query(BillItem)
            .filter(BillItem.bill_id == bill_id)
            .all()
        )

        if not items:
            raise ValueError("Cannot finalize an empty bill.")

        # If this is a credit sale, verify the customer.
        customer = None

        if bill.payment_method == "credit":
            customer = (
                db.query(Customer)
                .filter(Customer.id == bill.customer_id)
                .first()
            )

            if customer is None:
                raise ValueError("Customer not found.")

            if not customer.is_active:
                raise ValueError(
                    "Cannot create a credit sale for an inactive customer."
                )

        inventories = {}

        # Lock inventory rows and check stock.
        for item in items:
            inventory = (
                db.query(Inventory)
                .filter(Inventory.product_id == item.product_id)
                .with_for_update()
                .first()
            )

            if inventory is None:
                raise ValueError(
                    f"Inventory not found for product {item.product_id}."
                )

            if inventory.quantity < item.quantity:
                raise ValueError(
                    f"Insufficient stock for product {item.product_id}. "
                    f"Available: {inventory.quantity}, "
                    f"Requested: {item.quantity}"
                )

            inventories[item.product_id] = inventory

        # Reduce stock.
        for item in items:
            inventory = inventories[item.product_id]
            inventory.quantity -= item.quantity

        # Calculate totals.
        subtotal = Decimal("0.00")
        cgst = Decimal("0.00")
        sgst = Decimal("0.00")

        for item in items:
            subtotal += item.taxable_amount
            cgst += item.cgst
            sgst += item.sgst

        total_tax = cgst + sgst
        total = subtotal + total_tax

        bill.subtotal = subtotal
        bill.cgst = cgst
        bill.sgst = sgst
        bill.total_tax = total_tax
        bill.total = total

        bill.status = BillStatus.FINALIZED.value

        # Payment method must be selected before finalizing.
        if bill.payment_method is None:
            raise ValueError(
                "Payment method must be selected before finalizing."
            )

        payment = Payment(
            bill_id=bill.id,
            amount=total,
            method=bill.payment_method,
        )

        db.add(payment)

        # Credit sale:
        # Create the Khata entry inside the same transaction.
        if customer is not None:

            khata_entry = KhataEntry(
                customer_id=customer.id,
                bill_id=bill.id,
                entry_type=KhataEntryType.CREDIT.value,
                amount=total,
                note="Credit sale",
            )

            db.add(khata_entry)

        # One commit for everything.
        db.commit()
        db.refresh(bill)

        return bill

    except Exception:
        db.rollback()
        raise
