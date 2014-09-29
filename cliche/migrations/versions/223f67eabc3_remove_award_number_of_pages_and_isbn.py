"""remove award, number of pages, and isbn

Revision ID: 223f67eabc3
Revises: 4357a0df68d
Create Date: 2014-09-29 18:39:26.556967

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

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
    op.add_column('works',
                  sa.Column('isbn',
                            sa.VARCHAR(),
                            autoincrement=False,
                            nullable=True))
    op.add_column('works',
                  sa.Column('number_of_pages',
                            sa.INTEGER(),
                            autoincrement=False,
                            nullable=True))
    op.create_table(
        'awards',
        sa.Column('id',
                  sa.INTEGER(),
                  server_default="nextval('awards_id_seq'::regclass)",
                  nullable=False),
        sa.Column('name',
                  sa.VARCHAR(),
                  autoincrement=False,
                  nullable=False),
        sa.Column('created_at',
                  postgresql.TIMESTAMP(timezone=True),
                  autoincrement=False,
                  nullable=False),
        sa.PrimaryKeyConstraint('id', name='awards_pkey')
    )
    op.create_table(
        'work_awards',
        sa.Column('work_id',
                  sa.INTEGER(),
                  autoincrement=False,
                  nullable=False),
        sa.Column('award_id',
                  sa.INTEGER(),
                  autoincrement=False,
                  nullable=False),
        sa.Column('created_at',
                  postgresql.TIMESTAMP(timezone=True),
                  autoincrement=False,
                  nullable=False),
        sa.ForeignKeyConstraint(['award_id'],
                                ['awards.id'],
                                name='work_awards_award_id_fkey'),
        sa.ForeignKeyConstraint(['work_id'],
                                ['works.id'],
                                name='work_awards_work_id_fkey'),
        sa.PrimaryKeyConstraint('work_id',
                                'award_id',
                                name='work_awards_pkey')
    )
    op.create_table(
        'award_winners',
        sa.Column('person_id',
                  sa.INTEGER(),
                  autoincrement=False,
                  nullable=False),
        sa.Column('award_id',
                  sa.INTEGER(),
                  autoincrement=False,
                  nullable=False),
        sa.Column('created_at',
                  postgresql.TIMESTAMP(timezone=True),
                  autoincrement=False,
                  nullable=False),
        sa.ForeignKeyConstraint(['award_id'],
                                ['awards.id'],
                                name='award_winners_award_id_fkey'),
        sa.ForeignKeyConstraint(['person_id'],
                                ['people.id'],
                                name='award_winners_person_id_fkey'),
        sa.PrimaryKeyConstraint('person_id',
                                'award_id',
                                name='award_winners_pkey')
    )
