"""TVTropes models
 
Revision ID: 441c936f555
Revises: 1ed82ef0071
Create Date: 2014-08-08 03:42:59.602574
 
"""
from alembic import op
import sqlalchemy as sa
 
 
# revision identifiers, used by Alembic.
revision = '441c936f555'
down_revision = '1ed82ef0071'
 
 
def upgrade():
    op.create_table('tvtropes_entities',
    sa.Column('namespace', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('url', sa.String(), nullable=True),
    sa.Column('last_crawled', sa.DateTime(), nullable=True),
    sa.Column('type', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('namespace', 'name')
    )
    op.create_table('tvtropes_relations',
    sa.Column('origin_namespace', sa.String(), nullable=False),
    sa.Column('origin', sa.String(), nullable=False),
    sa.Column('destination_namespace', sa.String(), nullable=False),
    sa.Column('destination', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['origin_namespace', 'origin'], 
                            ['tvtropes_entities.namespace',
                            'tvtropes_entities.name'], ),
    sa.PrimaryKeyConstraint('origin_namespace', 'origin',
                            'destination_namespace', 'destination')
    )
 
 
def downgrade():
    op.drop_table('tvtropes_relations')
    op.drop_table('tvtropes_entities')
