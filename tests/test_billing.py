from decimal import Decimal

import pytest

from app.models.bill import BillStatus
from app.models.bill_item import BillItem
from app.models.inventory import Inventory
from app.models.payment import Payment
from app.models.khata_entry import KhataEntry, KhataEntryType
from app.models.product import Product

from app.services.billing_service import (
    create_bill,
    add_bill_item,
    calculate_bill,
    finalize_bill,
)
from app.services.khata_service import create_customer


def create_test_product(db, quantity=10):
    product = Product(
        sku="TEST001",
        name="Test Rice",
        category="Rice",
        unit="kg",
        selling_price=Decimal("75.00"),
        cost_price=Decimal("60.00"),
        gst_rate=Decimal("5.00"),
        hsn_code="1006",
        is_active=True,
    )

    db.add(product)
    db.flush()

    inventory = Inventory(
        product_id=product.id,
        quantity=Decimal(str(quantity)),
        reorder_level=Decimal("5.000"),
    )

    db.add(inventory)
    db.commit()

    db.refresh(product)
    db.refresh(inventory)

    return product, inventory


def test_create_draft_bill_does_not_reduce_stock(db):
    product, inventory = create_test_product(db, quantity=10)

    bill = create_bill(
        db=db,
        payment_method="cash",
    )

    add_bill_item(
        db=db,
        bill_id=bill.id,
        product_id=product.id,
        quantity=Decimal("2"),
    )

    db.refresh(inventory)

    assert bill.status == BillStatus.DRAFT.value
    assert inventory.quantity == Decimal("10.000")


def test_bill_calculates_gst_correctly(db):
    product, _ = create_test_product(db, quantity=10)

    bill = create_bill(
        db=db,
        payment_method="cash",
    )

    add_bill_item(
        db=db,
        bill_id=bill.id,
        product_id=product.id,
        quantity=Decimal("2"),
    )

    result = calculate_bill(db, bill.id)

    assert result.subtotal == Decimal("150.00")
    assert result.cgst == Decimal("3.75")
    assert result.sgst == Decimal("3.75")
    assert result.total_tax == Decimal("7.50")
    assert result.total == Decimal("157.50")


def test_finalize_bill_deducts_inventory_and_creates_payment(db):
    product, inventory = create_test_product(db, quantity=10)

    bill = create_bill(
        db=db,
        payment_method="cash",
    )

    add_bill_item(
        db=db,
        bill_id=bill.id,
        product_id=product.id,
        quantity=Decimal("2"),
    )

    result = finalize_bill(db, bill.id)

    db.refresh(bill)
    db.refresh(inventory)

    payment = (
        db.query(Payment)
        .filter(Payment.bill_id == bill.id)
        .first()
    )

    assert result.id == bill.id
    assert result.status == BillStatus.FINALIZED.value

    assert inventory.quantity == Decimal("8.000")

    assert payment is not None
    assert payment.amount == Decimal("157.50")
    assert payment.method == "cash"


def test_credit_bill_creates_khata_entry(db):
    product, _ = create_test_product(db, quantity=10)

    customer = create_customer(
        db=db,
        name="Test Customer",
        phone="9999999999",
    )

    bill = create_bill(
        db=db,
        customer_id=customer.id,
        payment_method="credit",
    )

    add_bill_item(
        db=db,
        bill_id=bill.id,
        product_id=product.id,
        quantity=Decimal("2"),
    )

    result = finalize_bill(db, bill.id)

    assert result.id == bill.id
    assert result.status == BillStatus.FINALIZED.value

    khata_entry = (
        db.query(KhataEntry)
        .filter(
            KhataEntry.customer_id == customer.id,
            KhataEntry.bill_id == bill.id,
            KhataEntry.entry_type == KhataEntryType.CREDIT.value,
        )
        .first()
    )

    assert khata_entry is not None
    assert khata_entry.amount == Decimal("157.50")


def test_finalize_bill_rejects_insufficient_stock(db):
    product, inventory = create_test_product(db, quantity=2)

    bill = create_bill(
        db=db,
        payment_method="cash",
    )

    add_bill_item(
        db=db,
        bill_id=bill.id,
        product_id=product.id,
        quantity=Decimal("5"),
    )

    with pytest.raises(ValueError, match="Insufficient stock"):
        finalize_bill(db, bill.id)

    db.refresh(inventory)
    db.refresh(bill)

    assert inventory.quantity == Decimal("2.000")
    assert bill.status == BillStatus.DRAFT.value


def test_multiple_products_are_calculated_correctly(db):
    product1, _ = create_test_product(db, quantity=10)

    product2 = Product(
        sku="TEST002",
        name="Test Sugar",
        category="Sugar",
        unit="kg",
        selling_price=Decimal("50.00"),
        cost_price=Decimal("40.00"),
        gst_rate=Decimal("5.00"),
        hsn_code="1701",
        is_active=True,
    )

    db.add(product2)
    db.flush()

    inventory2 = Inventory(
        product_id=product2.id,
        quantity=Decimal("20.000"),
        reorder_level=Decimal("5.000"),
    )

    db.add(inventory2)
    db.commit()

    bill = create_bill(
        db=db,
        payment_method="upi",
    )

    add_bill_item(
        db=db,
        bill_id=bill.id,
        product_id=product1.id,
        quantity=Decimal("2"),
    )

    add_bill_item(
        db=db,
        bill_id=bill.id,
        product_id=product2.id,
        quantity=Decimal("3"),
    )

    result = calculate_bill(db, bill.id)

    # Rice: 2 × 75 = 150
    # Sugar: 3 × 50 = 150
    # Subtotal = 300
    # GST 5% = 15
    # CGST = 7.50
    # SGST = 7.50
    # Total = 315

    assert result.subtotal == Decimal("300.00")
    assert result.cgst == Decimal("7.50")
    assert result.sgst == Decimal("7.50")
    assert result.total_tax == Decimal("15.00")
    assert result.total == Decimal("315.00")


def test_finalization_is_atomic_when_stock_is_insufficient(db):
    product1, inventory1 = create_test_product(db, quantity=10)

    product2 = Product(
        sku="TEST002",
        name="Test Oil",
        category="Oil",
        unit="litre",
        selling_price=Decimal("150.00"),
        cost_price=Decimal("120.00"),
        gst_rate=Decimal("5.00"),
        hsn_code="1512",
        is_active=True,
    )

    db.add(product2)
    db.flush()

    inventory2 = Inventory(
        product_id=product2.id,
        quantity=Decimal("1.000"),
        reorder_level=Decimal("5.000"),
    )

    db.add(inventory2)
    db.commit()

    bill = create_bill(
        db=db,
        payment_method="cash",
    )

    add_bill_item(
        db=db,
        bill_id=bill.id,
        product_id=product1.id,
        quantity=Decimal("2"),
    )

    add_bill_item(
        db=db,
        bill_id=bill.id,
        product_id=product2.id,
        quantity=Decimal("5"),
    )

    with pytest.raises(ValueError, match="Insufficient stock"):
        finalize_bill(db, bill.id)

    db.refresh(inventory1)
    db.refresh(inventory2)

    # Nothing should be deducted because finalization is atomic.
    assert inventory1.quantity == Decimal("10.000")
    assert inventory2.quantity == Decimal("1.000")