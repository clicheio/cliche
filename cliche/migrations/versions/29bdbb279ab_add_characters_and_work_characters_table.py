"""add characters and work_characters table

Revision ID: 29bdbb279ab
Revises: 123119b63b1
Create Date: 2014-10-31 01:09:54.927692

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '29bdbb279ab'
down_revision = '123119b63b1'


def upgrade():
    op.create_table(
        'characters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('original_character_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['id'], ['nameables.id']),
        sa.ForeignKeyConstraint(['original_character_id'], ['characters.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'work_characters',
        sa.Column('work_id', sa.Integer(), nullable=False),
        sa.Column('character_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id']),
        sa.ForeignKeyConstraint(['work_id'], ['works.id']),
        sa.PrimaryKeyConstraint('work_id', 'character_id')
    )


def downgrade():
    op.drop_table('work_characters')
    op.drop_table('characters')
