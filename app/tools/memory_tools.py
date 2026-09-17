from app.database.connection import SessionLocal

from app.services.memory_service import (
    save_preference,
    get_preference,
    get_all_preferences,
    delete_preference,
)


def save_owner_preference(
    key: str,
    value: str,
) -> dict:

    db = SessionLocal()

    try:

        preference = save_preference(
            db=db,
            key=key,
            value=value,
        )

        return {
            "success": True,
            "key": preference.key,
            "value": preference.value,
            "message": (
                f"Saved preference "
                f"'{preference.key}'."
            ),
        }

    except ValueError as e:

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()


def get_owner_preference(
    key: str,
) -> dict:

    db = SessionLocal()

    try:

        preference = get_preference(
            db=db,
            key=key,
        )

        if preference is None:

            return {
                "success": False,
                "message": (
                    f"No preference found "
                    f"for '{key}'."
                ),
            }

        return {
            "success": True,
            "key": preference.key,
            "value": preference.value,
        }

    finally:
        db.close()


def get_owner_preferences() -> dict:

    db = SessionLocal()

    try:

        preferences = get_all_preferences(
            db=db,
        )

        return {
            "success": True,
            "preferences": [
                {
                    "key": preference.key,
                    "value": preference.value,
                }
                for preference in preferences
            ],
        }

    finally:
        db.close()


def delete_owner_preference(
    key: str,
) -> dict:

    db = SessionLocal()

    try:

        deleted = delete_preference(
            db=db,
            key=key,
        )

        if not deleted:

            return {
                "success": False,
                "message": (
                    f"No preference found "
                    f"for '{key}'."
                ),
            }

        return {
            "success": True,
            "message": (
                f"Preference '{key}' deleted."
            ),
        }

    finally:
        db.close()