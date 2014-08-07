Database migration
==================

We are using Alembic_ for database migration.

.. _Alembic: https://alembic.readthedocs.org/


Get up to date
--------------

To upgrade the schema to the latest revision, simply run
:program:`cliche upgrade` command:

.. sourcecode:: console

   $ cliche -c dev.cfg upgrade
   INFO  [alembic.migration] Context impl PostgresqlImpl.
   INFO  [alembic.migration] Will assume transactional DDL.
   INFO  [alembic.migration] Running upgrade 256db34030b7 -> 2a1ebdf4c19e


Add a new revision
------------------

Each time you change the database schema, a new migration script has to be
added.  Use :program:`setup.py revision` command: 

.. sourcecode:: console

   $ python setup.py revision -c dev.cfg.py --autogenerate -m "add x to y"

.. note::

   You should use ``--autogenerate`` option to automatically generate
   a new migration script from delta between the actual database schema
   and the head migration script.  It does not 100% completely work well,
   you have to manually review a generated new migration script before
   commit it.

.. seealso::

   :ref:`ops` -- Alembic
      The reference of operations Alembic_ provides.


List revision history
---------------------

Use ``history`` command if you want to list all revisions of
the database migration history:

.. sourcecode:: console

   $ python setup.py history -c dev.cfg.py
   running history

   Rev: 1ed82ef0071 (head)
   Parent: 1344c33541b
   Path: /.../cliche/migrations/versions/1ed82ef0071_add_dod_column_to_person.py

       Add dod column to Person
       
       Revision ID: 1ed82ef0071
       Revises: 1344c33541b
       Create Date: 2014-08-04 21:48:04.403449

   Rev: 1344c33541b
   Parent: 2d8b17e13d1
   Path: /.../cliche/migrations/versions/1344c33541b_add_team_memberships_table.py

       Add team_memberships table
       
       Revision ID: 1344c33541b
       Revises: 2d8b17e13d1
       Create Date: 2014-02-27 03:05:00.853963

   Rev: 2d8b17e13d1
   Parent: 27e81ea4d86
   Path: /.../cliche/migrations/versions/2d8b17e13d1_add_teams_table.py

       Add teams table
       
       Revision ID: 2d8b17e13d1
       Revises: 27e81ea4d86
       Create Date: 2014-02-27 02:00:25.694782

   Rev: 27e81ea4d86
   Parent: None
   Path: /.../cliche/migrations/versions/27e81ea4d86_add_people_table.py

       Add people table
       
       Revision ID: 27e81ea4d86
       Revises: None
       Create Date: 2014-02-27 00:50:04.698519


Merge branches
--------------

The :program:`cliche upgrade` script will refuse to run any
migrations if there are two or more heads at a time:

.. sourcecode:: console

   $ cliche -c dev.cfg.py upgrade
   INFO  [alembic.context] Context class PostgresqlContext.
   INFO  [alembic.context] Will assume transactional DDL.
   Exception: Only a single head supported so far...

If you want to see how it's going on, list the history.  It would show
you there are two heads:

.. sourcecode:: console

   $ python setup.py history -c dev.cfg.py
   running history

   Rev: 2d8e07def2 (head)
   Parent: 1344c33541b
   Path: /.../cliche/migrations/versions/2d8e07def2_add_nationality_column_to_people_table.py

       Add nationality column to people table
       
       Revision ID: 2d8e07def2
       Revises: 1ed82ef0071
       Create Date: 2014-08-08 02:38:45.072148


   Rev: 1ed82ef0071 (head)
   Parent: 1344c33541b
   Path: /.../cliche/migrations/versions/1ed82ef0071_add_dod_column_to_person.py

       Add dod column to Person
       
       Revision ID: 1ed82ef0071
       Revises: 1344c33541b
       Create Date: 2014-08-04 21:48:04.403449

   Rev: 1344c33541b (branchpoint)
   Parent: 2d8b17e13d1
   Path: /.../cliche/migrations/versions/1344c33541b_add_team_memberships_table.py

       Add team_memberships table
       
       Revision ID: 1344c33541b
       Revises: 2d8b17e13d1
       Create Date: 2014-02-27 03:05:00.853963

   Rev: 2d8b17e13d1
   Parent: 27e81ea4d86
   Path: /.../cliche/migrations/versions/2d8b17e13d1_add_teams_table.py

       Add teams table
       
       Revision ID: 2d8b17e13d1
       Revises: 27e81ea4d86
       Create Date: 2014-02-27 02:00:25.694782

   Rev: 27e81ea4d86
   Parent: None
   Path: /.../cliche/migrations/versions/27e81ea4d86_add_people_table.py

       Add people table
       
       Revision ID: 27e81ea4d86
       Revises: None
       Create Date: 2014-02-27 00:50:04.698519

In this case you have to rebase one side's ``down_revisions`` to
another head::

    """Add nationality column to people table

    Revision ID: 2d8e07def2
    Revises: 1ed82ef0071  # changed from 1344c33541b
    Create Date: 2014-08-08 02:38:45.072148

    """

    # revision identifiers, used by Alembic.
    revision = '2d8e07def2'
    # changed from 1344c33541b
    down_revision = '1ed82ef0071'
