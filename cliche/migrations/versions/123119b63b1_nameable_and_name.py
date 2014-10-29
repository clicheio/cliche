"""nameable and name

Revision ID: 123119b63b1
Revises: 20362f93f52
Create Date: 2014-10-22 23:50:18.990020

"""
from alembic import context, op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '123119b63b1'
down_revision = '20362f93f52'

driver_name = context.get_bind().dialect.name


def upgrade():
    op.create_table(
        'nameables',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'names',
        sa.Column('nameable_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('reference_count', sa.Integer(), nullable=True),
        sa.Column('locale', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['nameable_id'], ['nameables.id'], ),
        sa.PrimaryKeyConstraint('nameable_id', 'name', 'locale')
    )

    op.create_foreign_key('franchises_id_fkey', 'franchises', 'nameables',
                          ['id'], ['id'])
    op.create_foreign_key('people_id_fkey', 'people', 'nameables',
                          ['id'], ['id'])
    op.create_foreign_key('teams_id_fkey', 'teams', 'nameables',
                          ['id'], ['id'])
    op.create_foreign_key('works_id_fkey', 'works', 'nameables',
                          ['id'], ['id'])
    op.create_foreign_key('worlds_id_fkey', 'worlds', 'nameables',
                          ['id'], ['id'])

    op.drop_column('franchises', 'name')
    op.drop_column('people', 'name')
    op.drop_column('teams', 'name')
    op.drop_column('works', 'name')
    op.drop_column('worlds', 'name')

    if driver_name == 'postgresql':
        op.execute("ALTER TABLE franchises ALTER COLUMN id DROP DEFAULT")
        op.execute("ALTER TABLE people ALTER COLUMN id DROP DEFAULT")
        op.execute("ALTER TABLE teams ALTER COLUMN id DROP DEFAULT")
        op.execute("ALTER TABLE works ALTER COLUMN id DROP DEFAULT")
        op.execute("ALTER TABLE worlds ALTER COLUMN id DROP DEFAULT")
        op.execute('DROP SEQUENCE franchises_id_seq')
        op.execute('DROP SEQUENCE people_id_seq')
        op.execute('DROP SEQUENCE teams_id_seq')
        op.execute('DROP SEQUENCE works_id_seq')
        op.execute('DROP SEQUENCE worlds_id_seq')


def downgrade():
    op.add_column('worlds', sa.Column('name', sa.String(), nullable=False))
    op.create_index('ix_worlds_name', 'worlds', ['name'], unique=False)

    op.add_column('works', sa.Column('name', sa.String(), nullable=False))
    op.create_index('ix_works_name', 'works', ['name'], unique=False)

    op.add_column('teams', sa.Column('name', sa.String(), nullable=True))
    op.create_index('ix_teams_name', 'teams', ['name'], unique=False)

    op.add_column('people', sa.Column('name', sa.String(), nullable=False))
    op.create_index('ix_people_name', 'people', ['name'], unique=False)

    op.add_column('franchises',
                  sa.Column('name', sa.String(), nullable=False))
    op.create_index('ix_franchises_name', 'franchises', ['name'],
                    unique=False)

    if driver_name == 'postgresql':
        op.execute('CREATE SEQUENCE franchises_id_seq')
        op.execute('CREATE SEQUENCE people_id_seq')
        op.execute('CREATE SEQUENCE teams_id_seq')
        op.execute('CREATE SEQUENCE works_id_seq')
        op.execute('CREATE SEQUENCE worlds_id_seq')
        op.execute("ALTER TABLE franchises ALTER COLUMN id "
                   "SET DEFAULT nextval('franchises_id_seq'::regclass)")
        op.execute("ALTER TABLE people ALTER COLUMN id "
                   "SET DEFAULT nextval('people_id_seq'::regclass)")
        op.execute("ALTER TABLE teams ALTER COLUMN id "
                   "SET DEFAULT nextval('teams_id_seq'::regclass)")
        op.execute("ALTER TABLE works ALTER COLUMN id "
                   "SET DEFAULT nextval('works_id_seq'::regclass)")
        op.execute("ALTER TABLE worlds ALTER COLUMN id "
                   "SET DEFAULT nextval('worlds_id_seq'::regclass)")

    op.drop_constraint('franchises_id_fkey', 'franchises', 'foreignkey')
    op.drop_constraint('people_id_fkey', 'people', 'foreignkey')
    op.drop_constraint('teams_id_fkey', 'teams', 'foreignkey')
    op.drop_constraint('works_id_fkey', 'works', 'foreignkey')
    op.drop_constraint('worlds_id_fkey', 'worlds', 'foreignkey')

    op.drop_table('names')
    op.drop_table('nameables')
