"""create external ids table

Revision ID: 8084c9ecd2
Revises: 6ea60f0db6
Create Date: 2014-11-14 23:19:53.507384

"""
from alembic import op
import sqlalchemy as sa


revision = '8084c9ecd2'
down_revision = '6ea60f0db6'


def upgrade():
    op.create_table(
        'external_ids',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('work_id', sa.Integer(), nullable=False),
        sa.Column('tvtropes_namespace', sa.String(), nullable=True),
        sa.Column('tvtropes_name', sa.String(), nullable=True),
        sa.Column('wikipedia_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ['tvtropes_namespace', 'tvtropes_name'],
            ['tvtropes_entities.namespace', 'tvtropes_entities.name'],
        ),
        sa.ForeignKeyConstraint(
            ['wikipedia_id'],
            ['wikipedia_entities.name'],
        ),
        sa.ForeignKeyConstraint(['work_id'], ['works.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('external_ids')
