"""Add dod column to Person

Revision ID: 1ed82ef0071
Revises: 1344c33541b
Create Date: 2014-08-04 21:48:04.403449

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1ed82ef0071'
down_revision = '1344c33541b'


def upgrade():
    op.add_column('people', sa.Column('dod', sa.Date(), nullable=True))


def downgrade():
    op.drop_column('people', 'dod')
