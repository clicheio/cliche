"""fix confidence type to float and add available column and indices
in edge tables

Revision ID: 4f96f94d94
Revises: 8084c9ecd2
Create Date: 2014-11-19 06:51:55.975882

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4f96f94d94'
down_revision = '8084c9ecd2'


def upgrade():
    op.add_column('cliche_tvtropes_edges',
                  sa.Column('available', sa.Boolean(), nullable=False))
    op.create_index(op.f('ix_cliche_tvtropes_edges_available'),
                    'cliche_tvtropes_edges',
                    ['available'],
                    unique=False)
    op.create_index(op.f('ix_cliche_tvtropes_edges_confidence'),
                    'cliche_tvtropes_edges',
                    ['confidence'],
                    unique=False)
    op.add_column('cliche_wikipedia_edge',
                  sa.Column('available', sa.Boolean(), nullable=False))
    op.create_index(op.f('ix_cliche_wikipedia_edge_available'),
                    'cliche_wikipedia_edge',
                    ['available'],
                    unique=False)
    op.create_index(op.f('ix_cliche_wikipedia_edge_confidence'),
                    'cliche_wikipedia_edge',
                    ['confidence'],
                    unique=False)
    op.alter_column(
        'cliche_tvtropes_edges',
        'confidence',
        existing_type=sa.Integer(),
        type_=sa.Float()
    )
    op.alter_column(
        'cliche_wikipedia_edge',
        'confidence',
        existing_type=sa.Integer(),
        type_=sa.Float()
    )


def downgrade():
    op.drop_index(op.f('ix_cliche_wikipedia_edge_confidence'),
                  table_name='cliche_wikipedia_edge')
    op.drop_index(op.f('ix_cliche_wikipedia_edge_available'),
                  table_name='cliche_wikipedia_edge')
    op.drop_column('cliche_wikipedia_edge', 'available')
    op.drop_index(op.f('ix_cliche_tvtropes_edges_confidence'),
                  table_name='cliche_tvtropes_edges')
    op.drop_index(op.f('ix_cliche_tvtropes_edges_available'),
                  table_name='cliche_tvtropes_edges')
    op.drop_column('cliche_tvtropes_edges', 'available')
    op.alter_column(
        'cliche_tvtropes_edges',
        'confidence',
        existing_type=sa.Float(),
        type_=sa.Integer()
    )
    op.alter_column(
        'cliche_wikipedia_edge',
        'confidence',
        existing_type=sa.Float(),
        type_=sa.Integer()
    )
