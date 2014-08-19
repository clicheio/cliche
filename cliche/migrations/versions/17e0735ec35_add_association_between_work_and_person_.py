"""add association between work and person with role

Revision ID: 17e0735ec35
Revises: 2e3e3a9a625
Create Date: 2014-08-20 01:25:53.368621

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '17e0735ec35'
down_revision = '2e3e3a9a625'


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
