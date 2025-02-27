"""First revision

Revision ID: 89d15ddcaa3b
Revises: 
Create Date: 2025-02-27 11:00:05.352945

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision: str = '89d15ddcaa3b'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('projects',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
    )

    op.create_table('users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.UniqueConstraint('email', name='uq_users_email')
    )

    op.create_table('user_project',
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id'), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), primary_key=True),
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=False, default=False),
        sa.UniqueConstraint('project_id', 'is_admin', name='_unique_admin_per_project')
    )

    op.create_table('documents',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False)
    )

    op.alter_column('projects', 'description',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('user_project', 'is_admin',
               existing_type=sa.BOOLEAN(),
               nullable=True)
    op.drop_constraint('_unique_admin_per_project', 'user_project', type_='unique')
    op.create_index('idx_admin_per_project', 'user_project', ['project_id'], unique=True, postgresql_where=sa.text('is_admin = true'))
    op.drop_column('user_project', 'id')


def downgrade() -> None:
    op.add_column('user_project', sa.Column('id', UUID(as_uuid=True), autoincrement=False, nullable=False))
    op.drop_index('idx_admin_per_project', table_name='user_project', postgresql_where=sa.text('is_admin = true'))
    op.create_unique_constraint('_unique_admin_per_project', 'user_project', ['project_id', 'is_admin'])
    op.alter_column('user_project', 'is_admin',
               existing_type=sa.BOOLEAN(),
               nullable=False)
    op.alter_column('projects', 'description',
               existing_type=sa.VARCHAR(),
               nullable=False)

    op.drop_table('documents')
    op.drop_table('user_project')
    op.drop_table('users')
    op.drop_table('projects')
