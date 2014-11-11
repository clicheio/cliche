"""add user and credentials

Revision ID: 5e043437da
Revises: 597dcb749d9
Create Date: 2014-11-11 22:36:15.582066

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5e043437da'
down_revision = '597dcb749d9'


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'credential',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'twitter_credential',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('identifier', sa.BigInteger(), nullable=False),
        sa.Column('token', sa.String(), nullable=True),
        sa.Column('token_secret', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['id'], ['credential.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('identifier')
    )


def downgrade():
    op.drop_table('twitter_credential')
    op.drop_table('credential')
    op.drop_table('users')
