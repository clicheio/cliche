"""add world, franchise, and director to role

Revision ID: 4357a0df68d
Revises: 30cf8c3e741
Create Date: 2014-09-23 22:00:09.463678

"""
from alembic import context, op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '4357a0df68d'
down_revision = '30cf8c3e741'

# setup for altering credits_role enum type
old_credits_role = sa.Enum(
    'artist', 'author', 'editor', 'unknown',
    name='credits_role'
)
new_credits_role = sa.Enum(
    'artist', 'author', 'editor', 'director', 'unknown',
    name='credits_role'
)
temp_credits_role = sa.Enum(
    'artist', 'author', 'editor', 'director', 'unknown',
    name='temp_credits_role'
)
driver_name = context.get_bind().dialect.name


def upgrade():
    # create worlds table
    op.create_table(
        'worlds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_worlds_name'), 'worlds', ['name'], unique=False)

    # create franchises table
    op.create_table(
        'franchises',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('world_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['world_id'], ['worlds.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_franchises_name'),
                    'franchises',
                    ['name'],
                    unique=False)

    # create work_franchises table
    op.create_table(
        'work_franchises',
        sa.Column('work_id', sa.Integer(), nullable=False),
        sa.Column('franchise_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['franchise_id'], ['franchises.id'], ),
        sa.ForeignKeyConstraint(['work_id'], ['works.id'], ),
        sa.PrimaryKeyConstraint('work_id', 'franchise_id')
    )

    # alter credits_role (add director)
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
    # alter credits_role (remove director)
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

    # drop work_franchises table
    op.drop_table('work_franchises')

    # drop franchises table
    op.drop_index(op.f('ix_franchises_name'), table_name='franchises')
    op.drop_table('franchises')
    if driver_name == 'postgresql':
        op.execute('DROP SEQUENCE franchises_id_seq')

    # drop worlds table
    op.drop_index(op.f('ix_worlds_name'), table_name='worlds')
    op.drop_table('worlds')
    if driver_name == 'postgresql':
        op.execute('DROP SEQUENCE worlds_id_seq')
