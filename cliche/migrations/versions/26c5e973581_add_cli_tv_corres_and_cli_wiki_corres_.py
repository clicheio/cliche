"""add cli_tv_corres and cli_wiki_corres table

Revision ID: 26c5e973581
Revises: 6ea60f0db6
Create Date: 2014-11-18 20:36:21.269893

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '26c5e973581'
down_revision = '6ea60f0db6'


def upgrade():
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


def downgrade():
    op.drop_table('cli_wiki_corres')
    op.drop_table('cli_tv_corres')
