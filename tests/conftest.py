import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database.base import Base

# Import all models so SQLAlchemy registers every table.
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.bill import Bill
from app.models.bill_item import BillItem
from app.models.customer import Customer
from app.models.khata_entry import KhataEntry
from app.models.payment import Payment
from app.models.owner_preference import OwnerPreference
from app.models.telegram_update import TelegramUpdate


@pytest.fixture
def db():
    """
    Creates an isolated PostgreSQL schema for each test.

    The normal public schema and existing KiranaAI demo data
    are never modified.
    """

    from app.database.connection import settings

    engine = create_engine(settings.DATABASE_URL)

    schema = f"test_{uuid.uuid4().hex[:12]}"

    connection = engine.connect()

    try:
        # Create isolated schema.
        connection.execute(
            text(f'CREATE SCHEMA "{schema}"')
        )
        connection.commit()

        # Create all application tables inside the test schema.
        connection.execution_options(
            schema_translate_map={None: schema}
        )

        test_connection = connection.execution_options(
            schema_translate_map={None: schema}
        )

        Base.metadata.create_all(test_connection)

        # IMPORTANT:
        # Commit table creation so a rollback inside a service test
        # cannot remove the temporary tables.
        connection.commit()

        SessionTesting = sessionmaker(
            bind=test_connection,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

        session = SessionTesting()

        # Make the temporary schema the active schema.
        session.execute(
            text(f'SET search_path TO "{schema}"')
        )
        session.commit()

        try:
            yield session

        finally:
            session.close()

    finally:
        # Drop only the temporary test schema.
        connection.execute(
            text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        )
        connection.commit()
        connection.close()
        engine.dispose()