from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.bill import Bill, BillStatus
from app.models.bill_item import BillItem
from app.models.khata_entry import KhataEntry, KhataEntryType
from app.models.product import Product
from app.models.inventory import Inventory


def get_day_close(
    db: Session,
    close_date: date,
) -> dict:

    start_datetime = datetime.combine(
        close_date,
        time.min,
    )

    next_day = close_date + timedelta(days=1)

    end_datetime = datetime.combine(
        next_day,
        time.min,
    )

    # ----------------------------------------
    # SALES
    # ----------------------------------------

    bills = (
        db.query(Bill)
        .filter(
            Bill.status == BillStatus.FINALIZED.value,
            Bill.created_at >= start_datetime,
            Bill.created_at < end_datetime,
        )
        .all()
    )

    bill_count = len(bills)

    total_sales = Decimal("0.00")
    cash_sales = Decimal("0.00")
    upi_sales = Decimal("0.00")
    card_sales = Decimal("0.00")
    credit_sales = Decimal("0.00")

    total_cgst = Decimal("0.00")
    total_sgst = Decimal("0.00")

    for bill in bills:

        total_sales += bill.total

        cash_sales += (
            bill.total
            if bill.payment_method == "cash"
            else Decimal("0.00")
        )

        upi_sales += (
            bill.total
            if bill.payment_method == "upi"
            else Decimal("0.00")
        )

        card_sales += (
            bill.total
            if bill.payment_method == "card"
            else Decimal("0.00")
        )

        credit_sales += (
            bill.total
            if bill.payment_method == "credit"
            else Decimal("0.00")
        )

        total_cgst += bill.cgst
        total_sgst += bill.sgst

    total_gst = total_cgst + total_sgst

    # ----------------------------------------
    # KHATA
    # ----------------------------------------

    khata_entries = (
        db.query(KhataEntry)
        .filter(
            KhataEntry.created_at >= start_datetime,
            KhataEntry.created_at < end_datetime,
        )
        .all()
    )

    credit_given_today = Decimal("0.00")
    khata_payments_today = Decimal("0.00")

    for entry in khata_entries:

        if entry.entry_type == KhataEntryType.CREDIT.value:
            credit_given_today += entry.amount

        elif entry.entry_type == KhataEntryType.PAYMENT.value:
            khata_payments_today += entry.amount

    # ----------------------------------------
    # LOW STOCK
    # ----------------------------------------

    low_stock_rows = (
        db.query(Product, Inventory)
        .join(
            Inventory,
            Inventory.product_id == Product.id,
        )
        .filter(
            Product.is_active == True,
            Inventory.quantity <= Inventory.reorder_level,
        )
        .order_by(
            Inventory.quantity.asc()
        )
        .all()
    )

    low_stock_products = []

    for product, inventory in low_stock_rows:

        low_stock_products.append(
            {
                "product_name": product.name,
                "quantity": str(inventory.quantity),
                "unit": product.unit,
                "reorder_level": str(inventory.reorder_level),
            }
        )

    # ----------------------------------------
    # BEST SELLING PRODUCT
    # ----------------------------------------

    best_selling = (
        db.query(
            Product.name,
            Product.unit,
            func.sum(BillItem.quantity).label(
                "total_quantity"
            ),
        )
        .join(
            BillItem,
            BillItem.product_id == Product.id,
        )
        .join(
            Bill,
            Bill.id == BillItem.bill_id,
        )
        .filter(
            Bill.status == BillStatus.FINALIZED.value,
            Bill.created_at >= start_datetime,
            Bill.created_at < end_datetime,
        )
        .group_by(
            Product.id,
            Product.name,
            Product.unit,
        )
        .order_by(
            func.sum(BillItem.quantity).desc()
        )
        .first()
    )

    best_selling_product = None

    if best_selling is not None:

        best_selling_product = {
            "product_name": best_selling[0],
            "unit": best_selling[1],
            "quantity": str(best_selling[2]),
        }

    # ----------------------------------------
    # FINAL RESULT
    # ----------------------------------------

    return {
        "date": close_date.isoformat(),

        "bill_count": bill_count,

        "total_sales": total_sales,

        "cash_sales": cash_sales,
        "upi_sales": upi_sales,
        "card_sales": card_sales,
        "credit_sales": credit_sales,

        "cgst": total_cgst,
        "sgst": total_sgst,
        "total_gst": total_gst,

        "credit_given_today": credit_given_today,
        "khata_payments_today": khata_payments_today,

        "low_stock_products": low_stock_products,

        "best_selling_product": best_selling_product,
    }
