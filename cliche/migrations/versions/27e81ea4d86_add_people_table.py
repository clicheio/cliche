"""Add people table

Revision ID: 27e81ea4d86
Revises: None
Create Date: 2014-02-27 00:50:04.698519

"""
from alembic import context
from alembic.op import (create_index, create_table,
                        drop_index, drop_table, execute)
from sqlalchemy.schema import Column, PrimaryKeyConstraint
from sqlalchemy.types import Date, DateTime, Integer, String


# revision identifiers, used by Alembic.
revision = '27e81ea4d86'
down_revision = None

driver_name = context.get_bind().dialect.name


def upgrade():
    create_table(
        'people',
        Column('id', Integer, nullable=False),
        Column('name', String, nullable=False),
        Column('dob', Date, nullable=True),
        Column('created_at', DateTime(timezone=True), nullable=False),
        PrimaryKeyConstraint('id')
    )
    create_index('ix_people_created_at', 'people', ['created_at'])
    create_index('ix_people_name', 'people', ['name'])


def downgrade():
    drop_index('ix_people_name', table_name='people')
    drop_index('ix_people_created_at', table_name='people')
    drop_table('people')
    if driver_name == 'postgresql':
        execute('DROP SEQUENCE people_id_seq')
