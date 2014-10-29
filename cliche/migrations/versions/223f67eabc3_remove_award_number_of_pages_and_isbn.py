"""remove award, number of pages, and isbn

Revision ID: 223f67eabc3
Revises: 4357a0df68d
Create Date: 2014-09-29 18:39:26.556967

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '223f67eabc3'
down_revision = '4357a0df68d'


def upgrade():
    op.drop_table('award_winners')
    op.drop_table('work_awards')
    op.drop_table('awards')

    op.drop_column('works', 'number_of_pages')
    op.drop_column('works', 'isbn')


def downgrade():
    op.add_column('works', sa.Column('isbn', sa.String(), nullable=True))
    op.add_column('works',
                  sa.Column('number_of_pages', sa.Integer(), nullable=True))

    op.create_table('awards',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('created_at', sa.DateTime(timezone=True),
                              nullable=False),
                    sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_awards_created_at'), 'awards', ['created_at'],
                    unique=False)
    op.create_index(op.f('ix_awards_name'), 'awards', ['name'], unique=False)

    op.create_table('work_awards',
                    sa.Column('work_id', sa.Integer(), nullable=False),
                    sa.Column('award_id', sa.Integer(), nullable=False),
                    sa.Column('created_at', sa.DateTime(timezone=True),
                              nullable=False),
                    sa.ForeignKeyConstraint(['award_id'], ['awards.id'], ),
                    sa.ForeignKeyConstraint(['work_id'], ['works.id'], ),
                    sa.PrimaryKeyConstraint('work_id', 'award_id'))

    op.create_table('award_winners',
                    sa.Column('person_id', sa.Integer(), nullable=False),
                    sa.Column('award_id', sa.Integer(), nullable=False),
                    sa.Column('created_at', sa.DateTime(timezone=True),
                              nullable=False),
                    sa.ForeignKeyConstraint(['award_id'], ['awards.id'], ),
                    sa.ForeignKeyConstraint(['person_id'], ['people.id'], ),
                    sa.PrimaryKeyConstraint('person_id', 'award_id'))
