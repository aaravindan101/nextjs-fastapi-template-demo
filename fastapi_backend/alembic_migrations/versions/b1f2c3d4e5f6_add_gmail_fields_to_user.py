"""Add Gmail fields to user

Revision ID: b1f2c3d4e5f6
Revises: a0de1e28652c
Create Date: 2025-11-04 23:41:43.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1f2c3d4e5f6'
down_revision: Union[str, None] = 'a0de1e28652c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add Gmail integration fields to user table
    op.add_column('user', sa.Column('last_pointer', sa.String(), nullable=True))
    op.add_column('user', sa.Column('onboarding_complete', sa.Integer(), server_default='0'))
    op.add_column('user', sa.Column('last_sync', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove Gmail integration fields from user table
    op.drop_column('user', 'last_sync')
    op.drop_column('user', 'onboarding_complete')
    op.drop_column('user', 'last_pointer')
