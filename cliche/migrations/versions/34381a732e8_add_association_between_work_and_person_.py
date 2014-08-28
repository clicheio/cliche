"""add association between work and person with role

Revision ID: 34381a732e8
Revises: 7f6fc70526
Create Date: 2014-08-29 03:58:16.570762

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '34381a732e8'
down_revision = '7f6fc70526'


def upgrade():
    op.create_table(
        'credits',
        sa.Column('work_id', sa.Integer(), nullable=False),
        sa.Column('person_id', sa.Integer(), nullable=False),
        sa.Column('role',
                  sa.Enum('Artist', 'Author', 'Editor', name='role'),
                  nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['person_id'], ['people.id'], ),
        sa.ForeignKeyConstraint(['work_id'], ['works.id'], ),
        sa.PrimaryKeyConstraint('work_id', 'person_id')
    )


def downgrade():
    op.drop_table('credits')
    # manually added this line for Enum type since autogenerate doesn't.
    sa.Enum(name='role').drop(op.get_bind())
