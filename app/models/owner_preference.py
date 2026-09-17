from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class OwnerPreference(Base):
    __tablename__ = "owner_preferences"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    key: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
