"""change work to relation, and add work to service/wikipedia

Revision ID: 4191a9189f0
Revises: 29bdbb279ab
Create Date: 2014-10-27 20:53:10.670786

"""
from alembic import op
import sqlalchemy as sa


revision = '4191a9189f0'
down_revision = '29bdbb279ab'


def upgrade():
    op.drop_table('wikipedia_works')
    op.create_table(
        'wikipedia_entities',
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('revision', sa.Integer(), nullable=True),
        sa.Column('label', sa.String(), nullable=True),
        sa.Column('country', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('name')
    )
    op.create_table(
        'wikipedia_relations',
        sa.Column('work', sa.String(), nullable=False),
        sa.Column('work_label', sa.String(), nullable=True),
        sa.Column('author', sa.String(), nullable=True),
        sa.Column('author_label', sa.String(), nullable=True),
        sa.Column('revision', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('work')
    )


def downgrade():
    op.drop_table('wikipedia_relations')
    op.drop_table('wikipedia_entities')
    op.create_table(
        'wikipedia_works',
        sa.Column('work', sa.String(), nullable=False),
        sa.Column('revision', sa.Integer(), nullable=True),
        sa.Column('author', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('work')
    )
