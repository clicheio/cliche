"""More robust Entity

Revision ID: 2fbf050c31f
Revises: 2e3e3a9a625
Create Date: 2014-08-15 01:54:53.986397

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2fbf050c31f'
down_revision = '2e3e3a9a625'


def upgrade():
    op.alter_column('tvtropes_entities', 'type',
                    existing_type=sa.VARCHAR(),
                    nullable=False)
    op.alter_column('tvtropes_entities', 'url',
                    existing_type=sa.VARCHAR(),
                    nullable=False)


def downgrade():
    op.alter_column('tvtropes_entities', 'url',
                    existing_type=sa.VARCHAR(),
                    nullable=True)
    op.alter_column('tvtropes_entities', 'type',
                    existing_type=sa.VARCHAR(),
                    nullable=True)
