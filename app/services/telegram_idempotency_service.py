from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.telegram_update import TelegramUpdate


def start_update(
    db: Session,
    update_id: int,
) -> tuple[bool, str | None]:

    existing = (
        db.query(TelegramUpdate)
        .filter(
            TelegramUpdate.update_id == update_id
        )
        .first()
    )

    if existing is not None:

        if existing.status == "completed":
            return False, existing.response

        if existing.status == "processing":
            return False, None

    record = TelegramUpdate(
        update_id=update_id,
        status="processing",
    )

    db.add(record)

    try:

        db.commit()

        return True, None

    except IntegrityError:

        db.rollback()

        existing = (
            db.query(TelegramUpdate)
            .filter(
                TelegramUpdate.update_id == update_id
            )
            .first()
        )

        if existing is not None:

            if existing.status == "completed":
                return False, existing.response

            return False, None

        raise


def complete_update(
    db: Session,
    update_id: int,
    response: str,
) -> None:

    record = (
        db.query(TelegramUpdate)
        .filter(
            TelegramUpdate.update_id == update_id
        )
        .first()
    )

    if record is None:
        return

    record.status = "completed"
    record.response = response
    record.completed_at = datetime.utcnow()

    db.commit()


def fail_update(
    db: Session,
    update_id: int,
) -> None:

    record = (
        db.query(TelegramUpdate)
        .filter(
            TelegramUpdate.update_id == update_id
        )
        .first()
    )

    if record is None:
        return

    db.delete(record)

    db.commit()