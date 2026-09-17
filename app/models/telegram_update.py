from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class TelegramUpdate(Base):
    __tablename__ = "telegram_updates"

    update_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="processing",
    )

    response: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )