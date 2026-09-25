from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.database.connection import SessionLocal
from app.models.bill import Bill
from app.models.bill_item import BillItem
from app.models.product import Product
from app.models.customer import Customer


# -------------------------------------------------
# REPORTLAB BUILT-IN FONTS
# -------------------------------------------------

ARIAL_FONT = "Helvetica"
ARIAL_BOLD_FONT = "Helvetica-Bold"


def generate_invoice_pdf(bill_id: int) -> str:

    db = SessionLocal()

    try:

        # -------------------------------------------------
        # GET BILL
        # -------------------------------------------------

        bill = (
            db.query(Bill)
            .filter(Bill.id == bill_id)
            .first()
        )

        if bill is None:
            raise ValueError(
                f"Bill {bill_id} not found."
            )

        if bill.status != "finalized":
            raise ValueError(
                "Invoice can only be generated "
                "for a finalized bill."
            )

        # -------------------------------------------------
        # GET BILL ITEMS
        # -------------------------------------------------

        items = (
            db.query(BillItem, Product)
            .join(
                Product,
                BillItem.product_id == Product.id
            )
            .filter(
                BillItem.bill_id == bill_id
            )
            .all()
        )

        if not items:
            raise ValueError(
                "Cannot generate invoice "
                "for an empty bill."
            )

        # -------------------------------------------------
        # GET CUSTOMER
        # -------------------------------------------------

        customer = None

        if bill.customer_id is not None:

            customer = (
                db.query(Customer)
                .filter(
                    Customer.id == bill.customer_id
                )
                .first()
            )

        # -------------------------------------------------
        # CREATE OUTPUT FOLDER
        # -------------------------------------------------

        output_folder = Path(
            "generated_invoices"
        )

        output_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        output_path = (
            output_folder
            / f"invoice_{bill.id}.pdf"
        )

        # -------------------------------------------------
        # PDF DOCUMENT
        # -------------------------------------------------

        document = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
        )

        styles = getSampleStyleSheet()

        # -------------------------------------------------
        # CUSTOM STYLES
        # -------------------------------------------------

        title_style = ParagraphStyle(
            "InvoiceTitle",
            parent=styles["Title"],
            fontName=ARIAL_BOLD_FONT,
            fontSize=20,
            leading=24,
        )

        heading_style = ParagraphStyle(
            "InvoiceHeading",
            parent=styles["Heading2"],
            fontName=ARIAL_BOLD_FONT,
            fontSize=15,
            leading=18,
        )

        normal_style = ParagraphStyle(
            "InvoiceNormal",
            parent=styles["Normal"],
            fontName=ARIAL_FONT,
            fontSize=10,
            leading=13,
        )

        bold_style = ParagraphStyle(
            "InvoiceBold",
            parent=styles["Normal"],
            fontName=ARIAL_BOLD_FONT,
            fontSize=10,
            leading=13,
        )

        story = []

        # -------------------------------------------------
        # HEADER
        # -------------------------------------------------

        story.append(
            Paragraph(
                "KiranaAI Supermarket",
                title_style,
            )
        )

        story.append(
            Paragraph(
                "GST Invoice",
                heading_style,
            )
        )

        story.append(
            Spacer(1, 8)
        )

        # -------------------------------------------------
        # BILL INFORMATION
        # -------------------------------------------------

        bill_date = bill.created_at

        customer_name = (
            customer.name
            if customer
            else "Walk-in Customer"
        )

        customer_phone = (
            customer.phone
            if customer and customer.phone
            else "-"
        )

        bill_information = [
            [
                Paragraph(
                    "<b>Invoice No.</b>",
                    bold_style
                ),
                Paragraph(
                    f"INV-{bill.id:05d}",
                    normal_style
                ),
            ],
            [
                Paragraph(
                    "<b>Date</b>",
                    bold_style
                ),
                Paragraph(
                    bill_date.strftime(
                        "%d-%m-%Y %I:%M %p"
                    ),
                    normal_style
                ),
            ],
            [
                Paragraph(
                    "<b>Customer</b>",
                    bold_style
                ),
                Paragraph(
                    customer_name,
                    normal_style
                ),
            ],
            [
                Paragraph(
                    "<b>Phone</b>",
                    bold_style
                ),
                Paragraph(
                    customer_phone,
                    normal_style
                ),
            ],
            [
                Paragraph(
                    "<b>Payment</b>",
                    bold_style
                ),
                Paragraph(
                    bill.payment_method or "-",
                    normal_style
                ),
            ],
        ]

        info_table = Table(
            bill_information,
            colWidths=[
                40 * mm,
                130 * mm,
            ],
        )

        info_table.setStyle(
            TableStyle(
                [
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, -1),
                        colors.lightgrey,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                ]
            )
        )

        story.append(info_table)

        story.append(
            Spacer(1, 12)
        )

        # -------------------------------------------------
        # ITEMS TABLE
        # -------------------------------------------------

        table_data = [
            [
                Paragraph("S.No", bold_style),
                Paragraph("Product", bold_style),
                Paragraph("HSN", bold_style),
                Paragraph("Qty", bold_style),
                Paragraph("Unit", bold_style),
                Paragraph("Price", bold_style),
                Paragraph("GST %", bold_style),
                Paragraph("Taxable", bold_style),
                Paragraph("Total", bold_style),
            ]
        ]

        for index, (item, product) in enumerate(
            items,
            start=1,
        ):

            table_data.append(
                [
                    Paragraph(
                        str(index),
                        normal_style
                    ),

                    Paragraph(
                        product.name,
                        normal_style
                    ),

                    Paragraph(
                        item.hsn_code or "-",
                        normal_style
                    ),

                    Paragraph(
                        str(item.quantity),
                        normal_style
                    ),

                    Paragraph(
                        product.unit,
                        normal_style
                    ),

                    Paragraph(
                        f"₹{item.unit_price:.2f}",
                        normal_style
                    ),

                    Paragraph(
                        f"{item.gst_rate:.2f}%",
                        normal_style
                    ),

                    Paragraph(
                        f"₹{item.taxable_amount:.2f}",
                        normal_style
                    ),

                    Paragraph(
                        f"₹{item.total_amount:.2f}",
                        normal_style
                    ),
                ]
            )

        items_table = Table(
            table_data,
            repeatRows=1,
            colWidths=[
                9 * mm,
                35 * mm,
                18 * mm,
                13 * mm,
                13 * mm,
                19 * mm,
                17 * mm,
                24 * mm,
                24 * mm,
            ],
        )

        items_table.setStyle(
            TableStyle(
                [
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.lightgrey,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "ALIGN",
                        (0, 0),
                        (-1, -1),
                        "CENTER",
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        3,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        3,
                    ),
                ]
            )
        )

        story.append(items_table)

        story.append(
            Spacer(1, 12)
        )

        # -------------------------------------------------
        # GST SUMMARY
        # -------------------------------------------------

        summary_data = [
            [
                Paragraph(
                    "Subtotal",
                    normal_style
                ),
                Paragraph(
                    f"₹{bill.subtotal:.2f}",
                    normal_style
                ),
            ],
            [
                Paragraph(
                    "CGST",
                    normal_style
                ),
                Paragraph(
                    f"₹{bill.cgst:.2f}",
                    normal_style
                ),
            ],
            [
                Paragraph(
                    "SGST",
                    normal_style
                ),
                Paragraph(
                    f"₹{bill.sgst:.2f}",
                    normal_style
                ),
            ],
            [
                Paragraph(
                    "Total Tax",
                    normal_style
                ),
                Paragraph(
                    f"₹{bill.total_tax:.2f}",
                    normal_style
                ),
            ],
            [
                Paragraph(
                    "<b>Grand Total</b>",
                    bold_style
                ),
                Paragraph(
                    f"<b>₹{bill.total:.2f}</b>",
                    bold_style
                ),
            ],
        ]

        summary_table = Table(
            summary_data,
            colWidths=[
                45 * mm,
                35 * mm,
            ],
            hAlign="RIGHT",
        )

        summary_table.setStyle(
            TableStyle(
                [
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "BACKGROUND",
                        (0, 4),
                        (-1, 4),
                        colors.lightgrey,
                    ),
                    (
                        "ALIGN",
                        (1, 0),
                        (1, -1),
                        "RIGHT",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                ]
            )
        )

        story.append(summary_table)

        story.append(
            Spacer(1, 15)
        )

        # -------------------------------------------------
        # FOOTER
        # -------------------------------------------------

        story.append(
            Paragraph(
                "Thank you for shopping with us!",
                normal_style,
            )
        )

        story.append(
            Paragraph(
                "Generated by KiranaAI",
                normal_style,
            )
        )

        # -------------------------------------------------
        # BUILD PDF
        # -------------------------------------------------

        document.build(story)

        return str(output_path)

    finally:
        db.close()