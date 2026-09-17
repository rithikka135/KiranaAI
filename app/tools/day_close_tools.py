from datetime import date

from app.database.connection import SessionLocal
from app.services.day_close_service import get_day_close


def get_day_close_tool() -> dict:

    db = SessionLocal()

    try:

        today = date.today()

        summary = get_day_close(
            db=db,
            close_date=today,
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

            "cgst": str(
                summary["cgst"]
            ),

            "sgst": str(
                summary["sgst"]
            ),

            "total_gst": str(
                summary["total_gst"]
            ),

            "credit_given_today": str(
                summary["credit_given_today"]
            ),

            "khata_payments_today": str(
                summary["khata_payments_today"]
            ),

            "low_stock_products": (
                summary["low_stock_products"]
            ),

            "best_selling_product": (
                summary["best_selling_product"]
            ),
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()
