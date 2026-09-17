from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        unique=True,
        nullable=False
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        nullable=False,
        default=0
    )

    reorder_level: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        nullable=False,
        default=5
    )