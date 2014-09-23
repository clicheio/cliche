"""add_role_to_primary_key_in_credit

Revision ID: 30cf8c3e741
Revises: 5308f49c79a
Create Date: 2014-09-16 12:07:31.035792

"""
from alembic import context, op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '30cf8c3e741'
down_revision = '5308f49c79a'

old_credits_role = sa.Enum(
    'artist', 'author', 'editor', name='credits_role'
)
new_credits_role = sa.Enum(
    'artist', 'author', 'editor', 'unknown', name='credits_role'
)
temp_credits_role = sa.Enum(
    'artist', 'author', 'editor', 'unknown', name='temp_credits_role'
)
driver_name = context.get_bind().dialect.name


def upgrade():
    if driver_name == 'postgresql':
        temp_credits_role.create(op.get_bind(), checkfirst=False)
        op.execute(
            'ALTER TABLE credits ALTER COLUMN role TYPE temp_credits_role'
            ' USING role::text::temp_credits_role'
        )
        old_credits_role.drop(op.get_bind(), checkfirst=False)
        new_credits_role.create(op.get_bind(), checkfirst=False)
        op.execute(
            'ALTER TABLE credits ALTER COLUMN role TYPE credits_role'
            ' USING role::text::credits_role'
        )
        temp_credits_role.drop(op.get_bind(), checkfirst=False)
    else:
        op.alter_column(
            'credits',
            'role',
            existing_type=old_credits_role,
            type_=new_credits_role,
        )


def downgrade():
    if driver_name == 'postgresql':
        temp_credits_role.create(op.get_bind(), checkfirst=False)
        op.execute(
            'ALTER TABLE credits ALTER COLUMN role TYPE temp_credits_role'
            ' USING role::text::temp_credits_role'
        )
        new_credits_role.drop(op.get_bind(), checkfirst=False)
        old_credits_role.create(op.get_bind(), checkfirst=False)
        op.execute(
            'ALTER TABLE credits ALTER COLUMN role TYPE credits_role'
            ' USING role::text::credits_role'
        )
        temp_credits_role.drop(op.get_bind(), checkfirst=False)
    else:
        op.alter_column(
            'credits',
            'role',
            existing_type=new_credits_role,
            type_=old_credits_role,
        )
