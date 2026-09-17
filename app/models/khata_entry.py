from decimal import Decimal
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database.base import Base


class KhataEntryType(str, Enum):
    CREDIT = "credit"
    PAYMENT = "payment"


class KhataEntry(Base):
    __tablename__ = "khata_entries"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False
    )

    bill_id: Mapped[int | None] = mapped_column(
        ForeignKey("bills.id"),
        nullable=True
    )

    entry_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )