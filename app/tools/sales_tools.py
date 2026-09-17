from datetime import date

from app.database.connection import SessionLocal
from app.services.sales_service import get_daily_sales


def get_today_sales_tool() -> dict:

    db = SessionLocal()

    try:

        today = date.today()

        summary = get_daily_sales(
            db=db,
            sales_date=today,
        )

        return {
            "success": True,
            "date": summary["date"],
            "bill_count": summary["bill_count"],
            "total_sales": str(
                summary["total_sales"]
            ),
            "cash_sales": str(
                summary["cash_sales"]
            ),
            "upi_sales": str(
                summary["upi_sales"]
            ),
            "card_sales": str(
                summary["card_sales"]
            ),
            "credit_sales": str(
                summary["credit_sales"]
            ),
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()