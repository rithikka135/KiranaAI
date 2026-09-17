from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.bill import Bill, BillStatus
from app.models.bill_item import BillItem
from app.models.product import Product
from app.models.inventory import Inventory


def get_weekly_analysis(
    db: Session,
    end_date: date | None = None,
) -> dict:
    """
    Generate sales and inventory analysis for the previous 7 days,
    including the supplied end_date.
    """

    if end_date is None:
        end_date = date.today()

    start_date = end_date - timedelta(days=6)

    start_datetime = datetime.combine(
        start_date,
        time.min,
    )

    end_datetime = datetime.combine(
        end_date + timedelta(days=1),
        time.min,
    )

    # --------------------------------------------------
    # FINALIZED BILLS
    # --------------------------------------------------

    bills = (
        db.query(Bill)
        .filter(
            Bill.status == BillStatus.FINALIZED.value,
            Bill.created_at >= start_datetime,
            Bill.created_at < end_datetime,
        )
        .all()
    )

    total_sales = Decimal("0.00")
    total_cgst = Decimal("0.00")
    total_sgst = Decimal("0.00")

    cash_sales = Decimal("0.00")
    upi_sales = Decimal("0.00")
    card_sales = Decimal("0.00")
    credit_sales = Decimal("0.00")

    daily_sales = {}

    for i in range(7):
        current_date = start_date + timedelta(days=i)
        daily_sales[current_date.isoformat()] = Decimal("0.00")

    for bill in bills:

        bill_total = bill.total or Decimal("0.00")

        total_sales += bill_total
        total_cgst += bill.cgst or Decimal("0.00")
        total_sgst += bill.sgst or Decimal("0.00")

        if bill.payment_method == "cash":
            cash_sales += bill_total

        elif bill.payment_method == "upi":
            upi_sales += bill_total

        elif bill.payment_method == "card":
            card_sales += bill_total

        elif bill.payment_method == "credit":
            credit_sales += bill_total

        bill_date = bill.created_at.date()

        if bill_date.isoformat() in daily_sales:
            daily_sales[bill_date.isoformat()] += bill_total

    total_gst = total_cgst + total_sgst

    # --------------------------------------------------
    # TOP SELLING PRODUCTS
    # --------------------------------------------------

    top_products_rows = (
        db.query(
            Product.name,
            Product.unit,
            func.sum(BillItem.quantity).label("total_quantity"),
            func.sum(BillItem.total_amount).label("total_revenue"),
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
            func.sum(BillItem.total_amount).desc()
        )
        .limit(10)
        .all()
    )

    top_products = []

    for row in top_products_rows:
        top_products.append(
            {
                "product_name": row[0],
                "unit": row[1],
                "quantity": str(row[2]),
                "revenue": str(row[3]),
            }
        )

    # --------------------------------------------------
    # LOW STOCK
    # --------------------------------------------------

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

    # --------------------------------------------------
    # TOTAL PRODUCT / INVENTORY COUNT
    # --------------------------------------------------

    total_products = (
        db.query(func.count(Product.id))
        .filter(Product.is_active == True)
        .scalar()
    )

    total_inventory_units = (
        db.query(func.coalesce(func.sum(Inventory.quantity), 0))
        .join(
            Product,
            Product.id == Inventory.product_id,
        )
        .filter(Product.is_active == True)
        .scalar()
    )

    # --------------------------------------------------
    # PAYMENT BREAKDOWN
    # --------------------------------------------------

    payment_breakdown = {
        "cash": str(cash_sales),
        "upi": str(upi_sales),
        "card": str(card_sales),
        "credit": str(credit_sales),
    }

    # --------------------------------------------------
    # INSIGHTS
    # --------------------------------------------------

    insights = []

    if total_sales > 0:

        payment_values = {
            "Cash": cash_sales,
            "UPI": upi_sales,
            "Card": card_sales,
            "Credit": credit_sales,
        }

        highest_payment = max(
            payment_values,
            key=payment_values.get,
        )

        insights.append(
            f"{highest_payment} was the largest payment mode "
            f"with sales of ₹{payment_values[highest_payment]:.2f}."
        )

    if top_products:

        top_product = top_products[0]

        insights.append(
            f"{top_product['product_name']} generated the highest "
            f"sales revenue at ₹{Decimal(top_product['revenue']):.2f}."
        )

    if low_stock_products:

        insights.append(
            f"{len(low_stock_products)} product(s) are currently "
            f"at or below their reorder level."
        )

    else:

        insights.append(
            "No products are currently at or below their reorder level."
        )

    if total_gst > 0:

        insights.append(
            f"Total GST collected during the period was "
            f"₹{total_gst:.2f}."
        )

    # --------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),

        "bill_count": len(bills),

        "total_sales": total_sales,

        "cash_sales": cash_sales,
        "upi_sales": upi_sales,
        "card_sales": card_sales,
        "credit_sales": credit_sales,

        "cgst": total_cgst,
        "sgst": total_sgst,
        "total_gst": total_gst,

        "daily_sales": {
            key: str(value)
            for key, value in daily_sales.items()
        },

        "payment_breakdown": payment_breakdown,

        "top_products": top_products,

        "low_stock_products": low_stock_products,

        "total_products": total_products or 0,

        "total_inventory_units": str(
            total_inventory_units or Decimal("0.00")
        ),

        "insights": insights,
    }