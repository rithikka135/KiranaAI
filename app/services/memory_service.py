from sqlalchemy.orm import Session

from app.models.owner_preference import OwnerPreference


def save_preference(
    db: Session,
    key: str,
    value: str,
) -> OwnerPreference:

    key = key.strip().lower()
    value = value.strip()

    if not key:
        raise ValueError(
            "Preference key cannot be empty."
        )

    if not value:
        raise ValueError(
            "Preference value cannot be empty."
        )

    preference = (
        db.query(OwnerPreference)
        .filter(
            OwnerPreference.key == key
        )
        .first()
    )

    if preference is None:

        preference = OwnerPreference(
            key=key,
            value=value,
        )

        db.add(preference)

    else:

        preference.value = value

    db.commit()
    db.refresh(preference)

    return preference


def get_preference(
    db: Session,
    key: str,
) -> OwnerPreference | None:

    key = key.strip().lower()

    return (
        db.query(OwnerPreference)
        .filter(
            OwnerPreference.key == key
        )
        .first()
    )


def get_all_preferences(
    db: Session,
) -> list[OwnerPreference]:

    return (
        db.query(OwnerPreference)
        .order_by(
            OwnerPreference.key.asc()
        )
        .all()
    )


def delete_preference(
    db: Session,
    key: str,
) -> bool:

    key = key.strip().lower()

    preference = (
        db.query(OwnerPreference)
        .filter(
            OwnerPreference.key == key
        )
        .first()
    )

    if preference is None:
        return False

    db.delete(preference)
    db.commit()

    return True
