from decimal import Decimal
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database.base import Base


class BillStatus(str, Enum):
    DRAFT = "draft"
    FINALIZED = "finalized"
    CANCELLED = "cancelled"


class Bill(Base):
    __tablename__ = "bills"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    customer_id: Mapped[int | None] = mapped_column(
    ForeignKey("customers.id"),
    nullable=True
    )

    payment_method: Mapped[str | None] = mapped_column(
    String(20),
    nullable=True
)
    
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=BillStatus.DRAFT.value
    )

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00")
    )

    cgst: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00")
    )

    sgst: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00")
    )

    total_tax: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00")
    )

    total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00")
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )