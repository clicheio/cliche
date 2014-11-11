"""make original name slug in tvtropes redirections not unique

Revision ID: 597dcb749d9
Revises: 29bdbb279ab
Create Date: 2014-11-11 21:07:26.151723

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '597dcb749d9'
down_revision = '29bdbb279ab'


def upgrade():
    op.drop_constraint(
        'tvtropes_redirections_pkey',
        'tvtropes_redirections',
        'primary'
    )
    op.create_primary_key(
        'tvtropes_redirections_pkey',
        'tvtropes_redirections',
        ['alias_namespace', 'alias_name']
    )


def downgrade():
    op.drop_constraint(
        'tvtropes_redirections_pkey',
        'tvtropes_redirections',
        'primary'
    )
    op.create_primary_key(
        'tvtropes_redirections_pkey',
        'tvtropes_redirections',
        [
            'alias_namespace',
            'alias_name',
            'original_namespace',
            'original_name'
        ]
    )
