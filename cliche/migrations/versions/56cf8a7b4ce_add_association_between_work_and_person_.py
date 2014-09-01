"""add association between work and person with role

Revision ID: 56cf8a7b4ce
Revises: 7f6fc70526
Create Date: 2014-09-01 21:16:35.758002

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '56cf8a7b4ce'
down_revision = '7f6fc70526'


def upgrade():
    credits_role = sa.Enum('artist', 'author', 'editor', name='credits_role')
    op.create_table(
        'credits',
        sa.Column('work_id', sa.Integer(), nullable=False),
        sa.Column('person_id', sa.Integer(), nullable=False),
        sa.Column('role', credits_role, nullable=True),
        sa.Column('created_at',
                  sa.DateTime(timezone=True),
                  nullable=False),
        sa.ForeignKeyConstraint(['person_id'], ['people.id'], ),
        sa.ForeignKeyConstraint(['work_id'], ['works.id'], ),
        sa.PrimaryKeyConstraint('work_id', 'person_id')
    )


def downgrade():
    op.drop_table('credits')
    # drop credits_role directly
    sa.Enum(name='credits_role').drop(op.get_bind(), checkfirst=False)
