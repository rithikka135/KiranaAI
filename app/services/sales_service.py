from datetime import datetime, date, time
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.bill import Bill, BillStatus


def get_daily_sales(
    db: Session,
    sales_date: date,
) -> dict:

    start_datetime = datetime.combine(
        sales_date,
        time.min,
    )

    end_datetime = datetime.combine(
        sales_date,
        time.max,
    )

    bills = (
        db.query(Bill)
        .filter(
            Bill.status == BillStatus.FINALIZED.value,
            Bill.created_at >= start_datetime,
            Bill.created_at <= end_datetime,
        )
        .all()
    )

    total_sales = Decimal("0.00")

    cash_sales = Decimal("0.00")
    upi_sales = Decimal("0.00")
    card_sales = Decimal("0.00")
    credit_sales = Decimal("0.00")

    for bill in bills:

        total_sales += bill.total

        if bill.payment_method == "cash":
            cash_sales += bill.total

        elif bill.payment_method == "upi":
            upi_sales += bill.total

        elif bill.payment_method == "card":
            card_sales += bill.total

        elif bill.payment_method == "credit":
            credit_sales += bill.total

    return {
        "date": sales_date.isoformat(),
        "bill_count": len(bills),
        "total_sales": total_sales,
        "cash_sales": cash_sales,
        "upi_sales": upi_sales,
        "card_sales": card_sales,
        "credit_sales": credit_sales,
    }