from app.documents.invoice_generator import generate_invoice_pdf


def generate_invoice_tool(
    bill_id: int,
) -> dict:
    """
    Generate a PDF invoice for an existing finalized bill.
    """

    try:
        pdf_path = generate_invoice_pdf(
            bill_id=bill_id
        )

        return {
            "success": True,
            "bill_id": bill_id,
            "pdf_path": pdf_path,
            "message": (
                f"Invoice for bill {bill_id} "
                f"generated successfully."
            ),
        }

    except ValueError as e:

        return {
            "success": False,
            "message": str(e),
        }

    except Exception as e:

        print("Invoice generation error:", e)

        return {
            "success": False,
            "message": (
                "Something went wrong while "
                "generating the invoice."
            ),
        }