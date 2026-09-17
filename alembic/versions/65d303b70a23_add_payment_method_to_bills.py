"""add payment method to bills

Revision ID: 65d303b70a23
Revises: 9ef50d32cd7a
Create Date: 2026-09-13 19:32:10.943207

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '65d303b70a23'
down_revision: Union[str, Sequence[str], None] = '9ef50d32cd7a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'bills',
        sa.Column(
            'payment_method',
            sa.String(length=20),
            nullable=True
        )
    )


def downgrade() -> None:
    op.drop_column(
        'bills',
        'payment_method'
    )
