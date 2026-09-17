from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ActiveBillSession(Base):
    __tablename__ = "active_bill_sessions"

    session_key: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    bill_id: Mapped[int] = mapped_column(
        Integer,
        unique=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )