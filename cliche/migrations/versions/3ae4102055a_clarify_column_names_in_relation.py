"""Clarify column names in Relation

Revision ID: 3ae4102055a
Revises: 2fbf050c31f
Create Date: 2014-08-18 22:30:58.780203

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '3ae4102055a'
down_revision = '2fbf050c31f'


def upgrade():
    op.alter_column('tvtropes_relations', 'origin',
                    new_column_name='origin_name')
    op.alter_column('tvtropes_relations', 'destination',
                    new_column_name='destination_name')


def downgrade():
    op.alter_column('tvtropes_relations', 'destination_name',
                    new_column_name='destination')
    op.alter_column('tvtropes_relations', 'origin_name',
                    new_column_name='origin')
