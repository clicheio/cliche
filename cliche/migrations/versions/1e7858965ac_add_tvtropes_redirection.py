"""Add tvtropes Redirection

Revision ID: 1e7858965ac
Revises: 2fbf050c31f
Create Date: 2014-08-15 02:05:16.802738

"""
from alembic.op import create_table, drop_table
from sqlalchemy.schema import (Column, ForeignKeyConstraint,
                               PrimaryKeyConstraint)
from sqlalchemy.types import String


# revision identifiers, used by Alembic.
revision = '1e7858965ac'
down_revision = '2fbf050c31f'


def upgrade():
    create_table(
        'tvtropes_redirections',
        Column('alias_namespace', String, nullable=False),
        Column('alias', String, nullable=False),
        Column('original_namespace', String, nullable=False),
        Column('original', String, nullable=False),
        ForeignKeyConstraint(['original_namespace', 'original'],
                             ['tvtropes_entities.namespace',
                              'tvtropes_entities.name'], ),
        PrimaryKeyConstraint('alias_namespace', 'alias',
                             'original_namespace', 'original')
    )


def downgrade():
    drop_table('tvtropes_redirections')
