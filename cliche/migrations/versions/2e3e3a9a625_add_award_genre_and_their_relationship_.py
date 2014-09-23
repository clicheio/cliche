"""Add award, genre and their relationship tables. Add columns to work.

Revision ID: 2e3e3a9a625
Revises: 441c936f555
Create Date: 2014-08-14 14:45:56.769052

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2e3e3a9a625'
down_revision = '441c936f555'


def upgrade():
    op.create_table('genres',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('created_at', sa.DateTime(timezone=True),
                              nullable=False),
                    sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_genres_created_at'), 'genres',
                    ['created_at'], unique=False)
    op.create_index(op.f('ix_genres_name'), 'genres', ['name'], unique=False)
    op.create_table('awards',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('created_at', sa.DateTime(timezone=True),
                              nullable=False),
                    sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_awards_created_at'), 'awards', ['created_at'],
                    unique=False)
    op.create_index(op.f('ix_awards_name'), 'awards', ['name'], unique=False)
    op.create_table('award_winners',
                    sa.Column('person_id', sa.Integer(), nullable=False),
                    sa.Column('award_id', sa.Integer(), nullable=False),
                    sa.Column('created_at', sa.DateTime(timezone=True),
                              nullable=False),
                    sa.ForeignKeyConstraint(['award_id'], ['awards.id'], ),
                    sa.ForeignKeyConstraint(['person_id'], ['people.id'], ),
                    sa.PrimaryKeyConstraint('person_id', 'award_id'))
    op.create_table('work_awards',
                    sa.Column('work_id', sa.Integer(), nullable=False),
                    sa.Column('award_id', sa.Integer(), nullable=False),
                    sa.Column('created_at', sa.DateTime(timezone=True),
                              nullable=False),
                    sa.ForeignKeyConstraint(['award_id'], ['awards.id'], ),
                    sa.ForeignKeyConstraint(['work_id'], ['works.id'], ),
                    sa.PrimaryKeyConstraint('work_id', 'award_id'))
    op.create_table('work_genres',
                    sa.Column('work_id', sa.Integer(), nullable=False),
                    sa.Column('genre_id', sa.Integer(), nullable=False),
                    sa.Column('created_at', sa.DateTime(timezone=True),
                              nullable=False),
                    sa.ForeignKeyConstraint(['genre_id'], ['genres.id'], ),
                    sa.ForeignKeyConstraint(['work_id'], ['works.id'], ),
                    sa.PrimaryKeyConstraint('work_id', 'genre_id'))
    op.add_column('works', sa.Column('isbn', sa.String(), nullable=True))
    op.add_column('works', sa.Column('number_of_pages', sa.Integer(),
                                     nullable=True))
    op.add_column('works', sa.Column('published_at', sa.Date(), nullable=True))
    op.drop_index('ix_works_title', table_name='works')
    op.alter_column('works', 'title', new_column_name='name')
    op.drop_column('works', 'dop')
    op.create_index(op.f('ix_works_created_at'), 'works', ['created_at'],
                    unique=False)
    op.create_index(op.f('ix_works_name'), 'works', ['name'], unique=False)


def downgrade():
    op.create_index('ix_works_title', 'works', ['title'], unique=False)
    op.drop_index(op.f('ix_works_name'), table_name='works')
    op.drop_index(op.f('ix_works_created_at'), table_name='works')
    op.add_column('works', sa.Column('dop', sa.DATE(), autoincrement=False,
                                     nullable=True))
    op.add_column('works', sa.Column('title', sa.VARCHAR(),
                                     autoincrement=False, nullable=False))
    op.drop_column('works', 'published_at')
    op.drop_column('works', 'number_of_pages')
    op.drop_column('works', 'name')
    op.drop_column('works', 'isbn')
    op.drop_table('work_genres')
    op.drop_table('work_awards')
    op.drop_table('award_winners')
    op.drop_index(op.f('ix_awards_name'), table_name='awards')
    op.drop_index(op.f('ix_awards_created_at'), table_name='awards')
    op.drop_table('awards')
    op.drop_index(op.f('ix_genres_name'), table_name='genres')
    op.drop_index(op.f('ix_genres_created_at'), table_name='genres')
    op.drop_table('genres')
