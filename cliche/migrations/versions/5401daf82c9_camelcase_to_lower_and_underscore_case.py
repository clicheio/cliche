"""camelCase to lower_and_underscore_case

Revision ID: 5401daf82c9
Revises: 2feaab75746
Create Date: 2014-11-09 22:18:42.737727

"""
from alembic import op
import sqlalchemy as sa


revision = '5401daf82c9'
down_revision = '2feaab75746'


def upgrade():
    op.add_column('wikipedia_entities',
                  sa.Column('main_character', sa.String(), nullable=True))
    op.add_column('wikipedia_entities',
                  sa.Column('notable_work', sa.String(), nullable=True))
    op.add_column('wikipedia_entities',
                  sa.Column('number_of_pages', sa.Integer(), nullable=True))
    op.add_column('wikipedia_entities',
                  sa.Column('previous_work', sa.String(), nullable=True))
    op.drop_column('wikipedia_entities', 'numberOfPages')
    op.drop_column('wikipedia_entities', 'mainCharacter')
    op.drop_column('wikipedia_entities', 'notableWork')
    op.drop_column('wikipedia_entities', 'previousWork')


def downgrade():
    op.add_column('wikipedia_entities',
                  sa.Column('previousWork', sa.VARCHAR(),
                            autoincrement=False, nullable=True))
    op.add_column('wikipedia_entities',
                  sa.Column('notableWork', sa.VARCHAR(),
                            autoincrement=False, nullable=True))
    op.add_column('wikipedia_entities',
                  sa.Column('mainCharacter', sa.VARCHAR(),
                            autoincrement=False, nullable=True))
    op.add_column('wikipedia_entities',
                  sa.Column('numberOfPages', sa.INTEGER(),
                            autoincrement=False, nullable=True))
    op.drop_column('wikipedia_entities', 'previous_work')
    op.drop_column('wikipedia_entities', 'number_of_pages')
    op.drop_column('wikipedia_entities', 'notable_work')
    op.drop_column('wikipedia_entities', 'main_character')
