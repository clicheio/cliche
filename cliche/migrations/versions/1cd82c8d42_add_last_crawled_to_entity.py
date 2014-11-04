"""add last_crawled to Entity

Revision ID: 1cd82c8d42
Revises: 2feaab75746
Create Date: 2014-11-04 21:33:14.225929

"""
from alembic import op
import sqlalchemy as sa


revision = '1cd82c8d42'
down_revision = '2feaab75746'


def upgrade():
    op.add_column('wikipedia_entities',
                  sa.Column('last_crawled',
                            sa.DateTime(timezone=True), nullable=False))


def downgrade():
    op.drop_column('wikipedia_works', 'last_crawled')
