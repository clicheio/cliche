"""Add teams table

Revision ID: 2d8b17e13d1
Revises: 27e81ea4d86
Create Date: 2014-02-27 02:00:25.694782

"""
from alembic.op import create_index, create_table, drop_index, drop_table
from sqlalchemy.schema import Column, PrimaryKeyConstraint
from sqlalchemy.types import DateTime, Integer, String


# revision identifiers, used by Alembic.
revision = '2d8b17e13d1'
down_revision = '27e81ea4d86'


def upgrade():
    create_table(
        'teams',
        Column('id', Integer, nullable=False),
        Column('name', String),
        Column('created_at', DateTime(timezone=True), nullable=False),
        PrimaryKeyConstraint('id')
    )
    create_index('ix_teams_created_at', 'teams', ['created_at'])
    create_index('ix_teams_name', 'teams', ['name'])


def downgrade():
    drop_index('ix_teams_name', table_name='teams')
    drop_index('ix_teams_created_at', table_name='teams')
    drop_table('teams')
