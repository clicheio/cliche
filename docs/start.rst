Getting started
===============

This tutorial covers how to get started with the Cliche codebase.


Prerequisites
-------------

Cliche is made with the following softwares:

Python_ 3.3 or higher
   Cliche is mostly written in Python language.  It's a high-level scripting
   language for general purpose.

Git_
   We use Git for version control.  We can track changes of Cliche source
   code using it.

   One of its main downsides is Windows support.  If you're not using Mac
   or Linux, it's hard to setup.  We recommend you to simply use
   `GitHub for Windows`_.

If you're using Mac you can find installers of these softwares in their
official websites.

If you're using Windows you can find CPython installer in Python_ website's
download page.  For Git, install `GitHub for Windows`_ as mentioned above.

You can install these softwares using APT if you're on Ubuntu or Debian Linux:

.. sourcecode:: console

   $ sudo apt-get install python3 git-core

There are other several third-party Python libraries as well, but you don't
have to install it by yourself.  These can be automatically resolved.

.. _Python: http://www.python.org/
.. _Git: http://git-scm.org/
.. _GitHub for Windows: http://windows.github.com/


Check out the source code
-------------------------

Cliche codebase is managed under GitHub_, so you can clone it using Git_:

.. sourcecode:: console

   $ git clone git@github.com:clicheio/cliche.git
   $ cd cliche/

If you're using Windows, you can clone it using `GitHub for Windows`_ as well.

.. _GitHub: https://github.com/clicheio/cliche


Create an environment
---------------------

The next step is creating an environment for Cliche.  This step should
be done first, and only once.

Each environment has its own directory for storing the :file:`site-packages`
folder, executable scripts, etc.  Here we assume that the name of environment
folder is :file:`cliche-env`:

.. sourcecode:: console

   $ pyvenv cliche-env


Enter the environment
---------------------

Each time you work on Cliche, you have to enter the created environment.  It's
applied to each terminal session.

.. note::
   
   If you're on Windows, you should *not* run the command prompt as
   administrator.

We assume here that the environment name is :file:`cliche-env` and
the repository name is :file:`cliche`.

.. sourcecode:: console

   $ . cliche-env/bin/activate
   (cliche-env) $

.. note::

   On Windows execute :program:`Scripts\\activate.bat` instead:

   .. sourcecode:: text

      C:\Users\John Doe> cliche-env\Scripts\activate.bat
      (cliche-env) C:\Users\John Doe>

The prefix ``(cliche-env)`` of the prompt indicates you're in the environment.
And then install Cliche's dependencies in the environment (instead of
system-wide :file:`site-packages`).

.. sourcecode:: console

   (cliche-env) $ cd cliche/ 
   (cliche-env) cliche$ pip install -e .


Resolve dependencies
--------------------

Cliche depends on several third-party Python libraries, and these can be
automatically resolved through :program:`pip` command:

.. sourcecode:: console

   $ pip install -e .
   Finished processing dependencies for Cliche==0.0.0


Configuration
-------------

To run web server a configuration file is required.  Here we assume
the filename we'll use is :file:`dev.cfg.py`.  Configuration file is
an ordinary Python script.  Create a new file and save::

    DATABASE_URL = 'postgresql:///cliche_db'


Relational database
-------------------

Cliche stores data into a relational database through SQLAlchemy_.
In production we use PostgreSQL_ and it also works well with SQLite_.

Python ships with SQLite.  There is no need to install it.
To use PostgreSQL, read :doc:`postgresql`.

Schema has to be created on the database.  Use :program:`cliche upgrade`
command:

.. sourcecode:: console

   $ cliche -c dev.cfg upgrade

.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _PostgreSQL: http://www.postgresql.org/
.. _SQLite: http://sqlite.org/
