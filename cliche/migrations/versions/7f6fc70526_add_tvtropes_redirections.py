"""Add tvtropes Redirections

Revision ID: 7f6fc70526
Revises: 3ae4102055a
Create Date: 2014-08-19 05:03:49.018915

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7f6fc70526'
down_revision = '3ae4102055a'


def upgrade():
    op.create_table(
        'tvtropes_redirections',
        sa.Column('alias_namespace', sa.String(), nullable=False),
        sa.Column('alias_name', sa.String(), nullable=False),
        sa.Column('original_namespace', sa.String(), nullable=False),
        sa.Column('original_name', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['original_namespace', 'original_name'],
                                ['tvtropes_entities.namespace',
                                 'tvtropes_entities.name'],
                                ),
        sa.PrimaryKeyConstraint('alias_namespace', 'alias_name',
                                'original_namespace', 'original_name')
    )


def downgrade():
    op.drop_table('tvtropes_redirections')
