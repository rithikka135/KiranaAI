from decimal import Decimal

import pytest

from app.models.product import Product
from app.models.inventory import Inventory
from app.models.customer import Customer

from app.services.khata_service import (
    create_customer,
    add_credit,
    get_customer_balance,
    record_khata_payment,
)


def create_test_product(
    db,
    sku="TEST001",
    name="Test Rice",
    selling_price=Decimal("75.00"),
    cost_price=Decimal("60.00"),
    gst_rate=Decimal("5.00"),
):
    product = Product(
        sku=sku,
        name=name,
        category="Test",
        unit="kg",
        selling_price=selling_price,
        cost_price=cost_price,
        gst_rate=gst_rate,
        hsn_code="1001",
        is_active=True,
    )

    db.add(product)
    db.flush()

    inventory = Inventory(
        product_id=product.id,
        quantity=Decimal("20.000"),
        reorder_level=Decimal("5.000"),
    )

    db.add(inventory)
    db.flush()

    return product, inventory


def test_product_and_inventory_are_created(db):
    product, inventory = create_test_product(db)

    assert product.id is not None
    assert product.name == "Test Rice"
    assert product.selling_price == Decimal("75.00")

    assert inventory.id is not None
    assert inventory.quantity == Decimal("20.000")
    assert inventory.reorder_level == Decimal("5.000")


def test_inventory_quantity_can_be_updated(db):
    product, inventory = create_test_product(db)

    inventory.quantity += Decimal("10.000")
    db.flush()

    assert inventory.quantity == Decimal("30.000")


def test_selling_price_rule(db):
    product, inventory = create_test_product(
        db,
        selling_price=Decimal("75.00"),
        cost_price=Decimal("60.00"),
    )

    assert product.selling_price >= product.cost_price


def test_customer_creation(db):
    customer = create_customer(
        db,
        name="Test Customer",
        phone="9000000000",
    )

    assert customer.id is not None
    assert customer.name == "Test Customer"
    assert customer.phone == "9000000000"


def test_khata_credit_and_payment(db):
    customer = create_customer(
        db,
        name="Ravi Test",
        phone="9000000001",
    )

    add_credit(
        db,
        customer_id=customer.id,
        amount=Decimal("467.00"),
        note="Test credit",
    )

    balance_before = get_customer_balance(
        db,
        customer_id=customer.id,
    )

    assert balance_before == Decimal("467.00")

    record_khata_payment(
        db,
        customer_id=customer.id,
        amount=Decimal("200.00"),
        note="Test payment",
    )

    balance_after = get_customer_balance(
        db,
        customer_id=customer.id,
    )

    assert balance_after == Decimal("267.00")


def test_khata_payment_cannot_exceed_balance(db):
    customer = create_customer(
        db,
        name="Payment Test",
        phone="9000000002",
    )

    add_credit(
        db,
        customer_id=customer.id,
        amount=Decimal("100.00"),
    )

    with pytest.raises(ValueError):
        record_khata_payment(
            db,
            customer_id=customer.id,
            amount=Decimal("150.00"),
        )

    balance = get_customer_balance(
        db,
        customer_id=customer.id,
    )

    assert balance == Decimal("100.00")


def test_khata_payment_must_be_positive(db):
    customer = create_customer(
        db,
        name="Positive Payment Test",
    )

    add_credit(
        db,
        customer_id=customer.id,
        amount=Decimal("100.00"),
    )

    with pytest.raises(ValueError):
        record_khata_payment(
            db,
            customer_id=customer.id,
            amount=Decimal("0.00"),
        )

    balance = get_customer_balance(
        db,
        customer_id=customer.id,
    )

    assert balance == Decimal("100.00")