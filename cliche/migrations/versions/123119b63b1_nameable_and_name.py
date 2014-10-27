"""nameable and name

Revision ID: 123119b63b1
Revises: 20362f93f52
Create Date: 2014-10-22 23:50:18.990020

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '123119b63b1'
down_revision = '20362f93f52'


def upgrade():
    op.create_table(
        'nameables',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'names',
        sa.Column('nameable_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('reference_count', sa.Integer(), nullable=True),
        sa.Column('locale', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['nameable_id'], ['nameables.id'], ),
        sa.PrimaryKeyConstraint('nameable_id', 'name', 'locale')
    )

    op.drop_column('franchises', 'name')
    op.drop_column('people', 'name')
    op.drop_column('teams', 'name')
    op.drop_column('works', 'name')
    op.drop_column('worlds', 'name')


def downgrade():
    op.add_column('worlds', sa.Column('name', sa.String(), nullable=False))
    op.create_index('ix_worlds_name', 'worlds', ['name'], unique=False)

    op.add_column('works', sa.Column('name', sa.String(), nullable=False))
    op.create_index('ix_works_name', 'works', ['name'], unique=False)

    op.add_column('teams', sa.Column('name', sa.String(), nullable=True))
    op.create_index('ix_teams_name', 'teams', ['name'], unique=False)

    op.add_column('people', sa.Column('name', sa.String(), nullable=False))
    op.create_index('ix_people_name', 'people', ['name'], unique=False)

    op.add_column('franchises', sa.Column('name', sa.String(), nullable=False))
    op.create_index('ix_franchises_name', 'franchises', ['name'], unique=False)

    op.drop_table('names')
    op.drop_table('nameables')
