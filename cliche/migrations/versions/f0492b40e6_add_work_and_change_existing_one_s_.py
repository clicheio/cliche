"""Add Work and change existing one's definition by using lambda

Revision ID: f0492b40e6
Revises: 223f67eabc3
Create Date: 2014-10-01 02:01:47.389283

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f0492b40e6'
down_revision = '223f67eabc3'

credits_role = postgresql.ENUM(
    'artist', 'author', 'editor', 'director', 'unknown', name='credits_role'
)


def upgrade():
    op.create_table(
        'wikipedia_works',
        sa.Column('work', sa.String(), nullable=False),
        sa.Column('author', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('work')
    )
    op.alter_column(
        'credits',
        'role',
        existing_type=credits_role,
        nullable=True
    )


def downgrade():
    op.alter_column(
        'credits',
        'role',
        existing_type=credits_role,
        nullable=True
    )
    op.drop_table('wikipedia_works')
