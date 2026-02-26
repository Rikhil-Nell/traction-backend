"""rename mode column to generation_mode

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-26 09:30:00.000000

"""
from typing import Sequence, Union
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename 'mode' column to 'generation_mode' to avoid PostgreSQL aggregate conflict."""
    op.alter_column('projects', 'mode', new_column_name='generation_mode')


def downgrade() -> None:
    """Revert column name back to 'mode'."""
    op.alter_column('projects', 'generation_mode', new_column_name='mode')
