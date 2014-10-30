"""ontology field added

Revision ID: 2feaab75746
Revises: 4191a9189f0
Create Date: 2014-10-30 02:42:11.730144

"""
from alembic import op
import sqlalchemy as sa


revision = '2feaab75746'
down_revision = '4191a9189f0'


def upgrade():
    op.add_column('wikipedia_entities',
                  sa.Column('author', sa.String(), nullable=True))
    op.add_column('wikipedia_entities',
                  sa.Column('director', sa.String(), nullable=True))
    op.add_column('wikipedia_entities',
                  sa.Column('illustrator', sa.String(), nullable=True))
    op.add_column('wikipedia_entities',
                  sa.Column('isbn', sa.String(), nullable=True))
    op.add_column('wikipedia_entities',
                  sa.Column('mainCharacter', sa.String(), nullable=True))
    op.add_column('wikipedia_entities',
                  sa.Column('notableWork', sa.String(), nullable=True))
    op.add_column('wikipedia_entities',
                  sa.Column('numberOfPages', sa.Integer(), nullable=True))
    op.add_column('wikipedia_entities',
                  sa.Column('previousWork', sa.String(), nullable=True))
    op.add_column('wikipedia_entities',
                  sa.Column('type', sa.String(length=20), nullable=True))
    op.add_column('wikipedia_entities',
                  sa.Column('writer', sa.String(), nullable=True))


def downgrade():
    op.drop_column('wikipedia_entities', 'writer')
    op.drop_column('wikipedia_entities', 'type')
    op.drop_column('wikipedia_entities', 'previousWork')
    op.drop_column('wikipedia_entities', 'numberOfPages')
    op.drop_column('wikipedia_entities', 'notableWork')
    op.drop_column('wikipedia_entities', 'mainCharacter')
    op.drop_column('wikipedia_entities', 'isbn')
    op.drop_column('wikipedia_entities', 'illustrator')
    op.drop_column('wikipedia_entities', 'director')
    op.drop_column('wikipedia_entities', 'author')
