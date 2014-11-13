"""add Trope

Revision ID: 6ea60f0db6
Revises: 5401daf82c9
Create Date: 2014-11-13 01:35:15.619898

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6ea60f0db6'
down_revision = '5401daf82c9'


def upgrade():
    op.create_table(
        'tropes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'work_tropes',
        sa.Column('work_id', sa.Integer(), nullable=False),
        sa.Column('trope_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['trope_id'], ['tropes.id'], ),
        sa.ForeignKeyConstraint(['work_id'], ['works.id'], ),
        sa.PrimaryKeyConstraint('work_id', 'trope_id')
    )
    op.add_column('works',
                  sa.Column('media_type', sa.String(), nullable=False))


def downgrade():
    op.drop_column('works', 'media_type')
    op.drop_table('work_tropes')
    op.drop_table('tropes')
