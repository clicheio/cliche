"""add wikiRevisionID to wikipedia_works

Revision ID: 20362f93f52
Revises: f0492b40e6
Create Date: 2014-10-12 12:11:10.685409

"""
from alembic import op
import sqlalchemy as sa

revision = '20362f93f52'
down_revision = 'f0492b40e6'


def upgrade():
    op.add_column(
        'wikipedia_works',
        sa.Column('revision', sa.String(), nullable=True)
    )


def downgrade():
    op.drop_column('wikipedia_works', 'revision')
