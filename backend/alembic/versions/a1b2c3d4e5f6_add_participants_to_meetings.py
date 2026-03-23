"""add_participants_to_meetings

Revision ID: a1b2c3d4e5f6
Revises: d4b6c660555b
Create Date: 2026-03-23 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "d4b6c660555b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("meetings", sa.Column("participants", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("meetings", "participants")
