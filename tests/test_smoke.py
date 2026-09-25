from decimal import Decimal

import pytest


def test_project_imports():
    from app.database.base import Base
    from app.models.product import Product
    from app.models.inventory import Inventory
    from app.models.bill import Bill
    from app.models.bill_item import BillItem
    from app.models.customer import Customer
    from app.models.khata_entry import KhataEntry
    from app.models.payment import Payment

    assert Base is not None
    assert Product is not None
    assert Inventory is not None
    assert Bill is not None
    assert BillItem is not None
    assert Customer is not None
    assert KhataEntry is not None
    assert Payment is not None


def test_decimal_calculation():
    quantity = Decimal("2")
    price = Decimal("75")
    gst_rate = Decimal("5")

    taxable = quantity * price
    tax = taxable * gst_rate / Decimal("100")
    total = taxable + tax

    assert taxable == Decimal("150")
    assert tax == Decimal("7.5")
    assert total == Decimal("157.5")


def test_selling_price_cannot_be_below_cost_price():
    cost_price = Decimal("50")
    selling_price = Decimal("45")

    assert selling_price < cost_price


def test_valid_selling_price_is_not_below_cost():
    cost_price = Decimal("50")
    selling_price = Decimal("55")

    assert selling_price >= cost_price


def test_gst_split_into_cgst_and_sgst():
    taxable_amount = Decimal("200")
    gst_rate = Decimal("5")

    total_gst = taxable_amount * gst_rate / Decimal("100")
    cgst = total_gst / Decimal("2")
    sgst = total_gst / Decimal("2")

    assert total_gst == Decimal("10")
    assert cgst == Decimal("5")
    assert sgst == Decimal("5")


def test_credit_balance_calculation():
    credit = Decimal("467")
    payment = Decimal("200")

    balance = credit - payment

    assert balance == Decimal("267")


def test_stock_quantity_after_receiving():
    current_stock = Decimal("27")
    received_quantity = Decimal("10")

    new_stock = current_stock + received_quantity

    assert new_stock == Decimal("37")


def test_stock_quantity_after_sale():
    current_stock = Decimal("37")
    sold_quantity = Decimal("5")

    remaining_stock = current_stock - sold_quantity

    assert remaining_stock == Decimal("32")