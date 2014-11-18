"""modify correspondence tables

Revision ID: 4ff1834aa21
Revises: 26c5e973581
Create Date: 2014-11-18 21:56:39.319294

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4ff1834aa21'
down_revision = '26c5e973581'


def upgrade():
    op.create_table(
        'cliche_tvtropes_edges',
        sa.Column('cliche_id', sa.Integer(), nullable=False),
        sa.Column('tvtropes_namespace', sa.String(), nullable=False),
        sa.Column('tvtropes_name', sa.String(), nullable=False),
        sa.Column('confidence', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['cliche_id'], ['works.id']),
        sa.ForeignKeyConstraint(['tvtropes_namespace',
                                 'tvtropes_name'],
                                ['tvtropes_entities.namespace',
                                 'tvtropes_entities.name']),
        sa.PrimaryKeyConstraint('cliche_id', 'tvtropes_namespace',
                                'tvtropes_name')
    )
    op.create_table(
        'cliche_wikipedia_edge',
        sa.Column('cliche_id', sa.Integer(), nullable=False),
        sa.Column('wikipedia_name', sa.String(), nullable=False),
        sa.Column('confidence', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['cliche_id'], ['works.id']),
        sa.ForeignKeyConstraint(['wikipedia_name'],
                                ['wikipedia_entities.name']),
        sa.PrimaryKeyConstraint('cliche_id', 'wikipedia_name')
    )
    op.drop_table('cli_wiki_corres')
    op.drop_table('cli_tv_corres')


def downgrade():
    op.create_table(
        'cli_tv_corres',
        sa.Column('cli_id', sa.Integer(), nullable=False),
        sa.Column('tv_namespace', sa.String(), nullable=False),
        sa.Column('tv_name', sa.String(), nullable=False),
        sa.Column('confidence', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['cli_id'], ['works.id']),
        sa.ForeignKeyConstraint(
            ['tv_namespace', 'tv_name'],
            ['tvtropes_entities.namespace', 'tvtropes_entities.name']
        ),
        sa.PrimaryKeyConstraint('cli_id', 'tv_namespace', 'tv_name')
    )
    op.create_table(
        'cli_wiki_corres',
        sa.Column('cli_id', sa.Integer(), nullable=False),
        sa.Column('wiki_name', sa.String(), nullable=False),
        sa.Column('confidence', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['cli_id'], ['works.id']),
        sa.ForeignKeyConstraint(['wiki_name'], ['wikipedia_entities.name']),
        sa.PrimaryKeyConstraint('cli_id', 'wiki_name')
    )
    op.drop_table('cliche_wikipedia_edge')
    op.drop_table('cliche_tvtropes_edges')
