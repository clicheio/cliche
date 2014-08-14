"""TVTropes models

Revision ID: 441c936f555
Revises: 57fc5e85328 # changed from 1ed82ef0071
Create Date: 2014-08-08 03:42:59.602574

"""
from alembic.op import create_table, drop_table
from sqlalchemy.schema import (Column, ForeignKeyConstraint,
                               PrimaryKeyConstraint)
from sqlalchemy.types import DateTime, String


# revision identifiers, used by Alembic.
revision = '441c936f555'
down_revision = '57fc5e85328'


def upgrade():
    create_table(
        'tvtropes_entities',
        Column('namespace', String, nullable=False),
        Column('name', String, nullable=False),
        Column('url', String, nullable=True),
        Column('last_crawled', DateTime, nullable=True),
        Column('type', String, nullable=True),
        PrimaryKeyConstraint('namespace', 'name')
    )
    create_table(
        'tvtropes_relations',
        Column('origin_namespace', String(), nullable=False),
        Column('origin', String(), nullable=False),
        Column('destination_namespace', String(), nullable=False),
        Column('destination', String, nullable=False),
        ForeignKeyConstraint(['origin_namespace', 'origin'],
                             ['tvtropes_entities.namespace',
                             'tvtropes_entities.name'], ),
        PrimaryKeyConstraint('origin_namespace', 'origin',
                             'destination_namespace', 'destination')
    )


def downgrade():
    drop_table('tvtropes_relations')
    drop_table('tvtropes_entities')
