"""remove relationship between work and team, and add team_id to credit

Revision ID: 5308f49c79a
Revises: 56cf8a7b4ce
Create Date: 2014-09-10 19:03:18.993659

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5308f49c79a'
down_revision = '56cf8a7b4ce'


def upgrade():
    op.add_column('credits', sa.Column('team_id', sa.Integer(), nullable=True))
    op.create_foreign_key("credits_team_id_fkey", "credits", "teams",
                          ["team_id"], ["id"])
    op.drop_column('works', 'team_id')


def downgrade():
    op.add_column('works', sa.Column('team_id', sa.Integer(),
                                     autoincrement=False, nullable=True))
    op.create_foreign_key("works_team_id_fkey", "works", "teams",
                          ["team_id"], ["id"])
    op.drop_column('credits', 'team_id')
