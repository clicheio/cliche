"""Add team_memberships table

Revision ID: 1344c33541b
Revises: 2d8b17e13d1
Create Date: 2014-02-27 03:05:00.853963

"""
from alembic.op import create_table, drop_table
from sqlalchemy.schema import (Column, ForeignKeyConstraint,
                               PrimaryKeyConstraint)
from sqlalchemy.types import DateTime, Integer


# revision identifiers, used by Alembic.
revision = '1344c33541b'
down_revision = '2d8b17e13d1'


def upgrade():
    create_table(
        'team_memberships',
        Column('team_id', Integer, nullable=False),
        Column('member_id', Integer, nullable=False),
        Column('created_at', DateTime(timezone=True), nullable=False),
        ForeignKeyConstraint(['member_id'], ['people.id']),
        ForeignKeyConstraint(['team_id'], ['teams.id']),
        PrimaryKeyConstraint('team_id', 'member_id')
    )


def downgrade():
    drop_table('team_memberships')
