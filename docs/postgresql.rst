Setup PostgreSQL
================

We use PostgreSQL_ for Cliche in the production.  PostgreSQL is the most
powerful open-source relational database system in the world.

To build up your local development environment near production, we recommend
you also to install PostgreSQL in your local box.

.. _PostgreSQL: http://postgresql.org/


Install PostgreSQL
------------------

Mac
```

`Postgres.app`_ must be the easiest way to install PostgreSQL on your Mac.
Go, download, and install.

Then, create a role and a database.

.. sourcecode:: console

   $ createuser -s `whoami`
   $ createdb cliche_db -E utf8 -T postgres

.. _Postgres.app: http://postgresapp.com/


Ubuntu/Debian Linux
```````````````````

Install it using APT, and then create a role and a database.

.. sourcecode:: console

   $ sudo apt-get install postgresql
   $ sudo -u postgres createuser -s `whoami`
   $ createdb cliche_db -E utf8 -T postgres


Connect from Python
-------------------

Install :mod:`psycopg2` using APT (if you're on Ubuntu/Debian):

.. sourcecode:: console

   $ sudo apt-get install python-psycopg2

Or you can install it using :program:`pip`, of course.  However you
have to install libpq (including its headers) and CPython headers to link
first.  These things can be installed using APT as well if you're on Ubuntu or
Debian:

.. sourcecode:: console

   $ sudo apt-get install libpq libpq-dev python-dev

Or :program:`yum` if you're CentOS/Fedora/RHEL:

.. sourcecode:: console

   $ sudo yum install postgresql-libs postgresql-devel python-devel

And then run :program:`pip`:

.. sourcecode:: console

   $ pip install psycopg2


Configuration
-------------

::

    DATABASE_URL = 'postgresql:///cliche_db'

