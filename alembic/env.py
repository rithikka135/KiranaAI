from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

from app.database.base import Base
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.bill import Bill
from app.models.bill_item import BillItem
from app.database.connection import settings
from app.models.owner_preference import OwnerPreference
from app.models.telegram_update import TelegramUpdate
from app.models.active_bill_session import ActiveBillSession


# Alembic Config object
config = context.config


# Set up logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# Tell Alembic about our SQLAlchemy models
target_metadata = Base.metadata


# Get database URL from .env
config.set_main_option(
    "sqlalchemy.url",
    settings.DATABASE_URL
)


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode."""

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()