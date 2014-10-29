"""add work

Revision ID: 57fc5e85328
Revises: 1ed82ef0071
Create Date: 2014-08-08 00:16:41.428095

"""
from alembic import context, op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '57fc5e85328'
down_revision = '1ed82ef0071'

driver_name = context.get_bind().dialect.name


def upgrade():
    op.create_table(
        'works',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('dop', sa.Date(), nullable=True),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_works_title'), 'works', ['title'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_works_title'), table_name='works')
    op.drop_table('works')
    if driver_name == 'postgresql':
        op.execute('DROP SEQUENCE works_id_seq')
