"""add award, genre, and columns to work

Revision ID: 23855972dea
Revises: 441c936f555
Create Date: 2014-08-11 02:49:57.027825

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '23855972dea'
down_revision = '441c936f555'


def upgrade():
    op.create_table('genres',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('created_at',
                              sa.DateTime(timezone=True),
                              nullable=False),
                    sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_genres_name'), 'genres', ['name'], unique=False)
    op.create_table('awards',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('created_at',
                              sa.DateTime(timezone=True),
                              nullable=False),
                    sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_awards_name'), 'awards', ['name'], unique=False)
    op.create_table('person_awards',
                    sa.Column('person_id', sa.Integer(), nullable=False),
                    sa.Column('award_id', sa.Integer(), nullable=False),
                    sa.Column('created_at',
                              sa.DateTime(timezone=True), nullable=False),
                    sa.ForeignKeyConstraint(['award_id'], ['awards.id'], ),
                    sa.ForeignKeyConstraint(['person_id'], ['people.id'], ),
                    sa.PrimaryKeyConstraint('person_id', 'award_id'))
    op.create_table('work_genres',
                    sa.Column('work_id', sa.Integer(), nullable=False),
                    sa.Column('genre_id', sa.Integer(), nullable=False),
                    sa.Column('created_at',
                              sa.DateTime(timezone=True), nullable=False),
                    sa.ForeignKeyConstraint(['genre_id'], ['genres.id'], ),
                    sa.ForeignKeyConstraint(['work_id'], ['works.id'], ),
                    sa.PrimaryKeyConstraint('work_id', 'genre_id'))
    op.create_table('work_awards',
                    sa.Column('work_id', sa.Integer(), nullable=False),
                    sa.Column('award_id', sa.Integer(), nullable=False),
                    sa.Column('created_at',
                              sa.DateTime(timezone=True), nullable=False),
                    sa.ForeignKeyConstraint(['award_id'], ['awards.id'], ),
                    sa.ForeignKeyConstraint(['work_id'], ['works.id'], ),
                    sa.PrimaryKeyConstraint('work_id', 'award_id'))
    op.add_column('works', sa.Column('isbn', sa.String(), nullable=True))
    op.add_column('works', sa.Column('name', sa.String(), nullable=False))
    op.add_column('works', sa.Column('number_of_pages',
                                     sa.Integer(),
                                     nullable=True))
    op.add_column('works', sa.Column('publication_date',
                                     sa.Date(),
                                     nullable=True))
    op.drop_column('works', 'dop')
    op.drop_column('works', 'title')
    op.create_index(op.f('ix_works_created_at'),
                    'works', ['created_at'], unique=False)
    op.create_index(op.f('ix_works_name'), 'works', ['name'], unique=False)
    op.drop_index('ix_works_title', table_name='works')


def downgrade():
    op.create_index('ix_works_title', 'works', ['title'], unique=False)
    op.drop_index(op.f('ix_works_name'), table_name='works')
    op.drop_index(op.f('ix_works_created_at'), table_name='works')
    op.add_column('works', sa.Column('title',
                                     sa.VARCHAR(),
                                     autoincrement=False,
                                     nullable=False))
    op.add_column('works', sa.Column('dop',
                                     sa.DATE(),
                                     autoincrement=False,
                                     nullable=True))
    op.drop_column('works', 'publication_date')
    op.drop_column('works', 'number_of_pages')
    op.drop_column('works', 'name')
    op.drop_column('works', 'isbn')
    op.drop_table('work_awards')
    op.drop_table('work_genres')
    op.drop_table('person_awards')
    op.drop_index(op.f('ix_awards_name'), table_name='awards')
    op.drop_table('awards')
    op.drop_index(op.f('ix_genres_name'), table_name='genres')
    op.drop_table('genres')
