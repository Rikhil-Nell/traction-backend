"""add mode, llms_txt, ai_json, fields, and unique constraint

Revision ID: a1b2c3d4e5f6
Revises: 3c8ab4c93fd2
Create Date: 2026-02-26 07:00:00.000000

"""
from typing import Sequence, Union
import sqlmodel
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '3c8ab4c93fd2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Project: add new columns
    op.add_column('projects', sa.Column('mode', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False, server_default='doc'))
    op.add_column('projects', sa.Column('llms_txt', sa.Text(), nullable=True))
    op.add_column('projects', sa.Column('ai_json', sa.JSON(), nullable=True))
    op.add_column('projects', sa.Column('last_generation_fields_hash', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=True))

    # Project: add unique constraint on (user_id, name)
    op.create_unique_constraint('uq_user_project_name', 'projects', ['user_id', 'name'])

    # ProjectDocument: add fields column
    op.add_column('project_documents', sa.Column('fields', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('project_documents', 'fields')
    op.drop_constraint('uq_user_project_name', 'projects', type_='unique')
    op.drop_column('projects', 'last_generation_fields_hash')
    op.drop_column('projects', 'ai_json')
    op.drop_column('projects', 'llms_txt')
    op.drop_column('projects', 'mode')
