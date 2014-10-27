"""add wikipedia_works

Revision ID: 11f224ecae
Revises: 123119b63b1
Create Date: 2014-10-27 20:35:11.625612

"""
from alembic import op
import sqlalchemy as sa


revision = '11f224ecae'
down_revision = '123119b63b1'


def upgrade():
    op.create_table(
        'wikipedia_works',
        sa.Column('work', sa.String(), nullable=False),
        sa.Column('revision', sa.Integer(), nullable=True),
        sa.Column('author', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('work')
    )


def downgrade():
    op.drop_table('wikipedia_works')
