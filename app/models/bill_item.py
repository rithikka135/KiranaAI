from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class BillItem(Base):
    __tablename__ = "bill_items"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    bill_id: Mapped[int] = mapped_column(
        ForeignKey("bills.id"),
        nullable=False
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        nullable=False
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    gst_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False
    )

    taxable_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    cgst: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    sgst: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    hsn_code: Mapped[str | None] = mapped_column(
    String(20),
    nullable=True,
)  