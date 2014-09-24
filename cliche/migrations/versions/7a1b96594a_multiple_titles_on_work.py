"""multiple titles on work

Revision ID: 7a1b96594a
Revises: 4357a0df68d
Create Date: 2014-09-24 23:35:36.040641

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '7a1b96594a'
down_revision = '4357a0df68d'


def upgrade():
    # drop name column in works table
    op.drop_index('ix_works_name', table_name='works')
    op.drop_column('works', 'name')

    # create titles table
    op.create_table(
        'titles',
        sa.Column('work_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('reference_count', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['work_id'], ['works.id'], ),
        sa.PrimaryKeyConstraint('work_id', 'title')
    )


def downgrade():
    # add name column to works table
    op.add_column(
        'works',
        sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=False)
    )
    op.create_index('ix_works_name', 'works', ['name'], unique=False)

    # drop titles table
    op.drop_table('titles')
