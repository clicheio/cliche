Testing
=======

:file:`tests/`
--------------

The test suite for Cliche is in :file:`tests/` directory.
All Python source files with :file:`_test.py` suffix are executed by
:pypi:`pytest` framework.


Running tests
-------------

You can run tests using :program:`setup.py` script or :program:`py.test`
command which is provided :pypi:`pytest` package:

.. code-block:: console

   $ python setup.py test
   $ py.test

two ways provide slightly different features:

``python setup.py test``
   It installs dependencies including testing libraries like :pypi:`pytest`
   first if these are not completely resolved yet.
   It only supports very basic :ref:`test-settings` thorugh environment
   variables.

:program:`py.test`
   You have to install packages for testing e.g. :pypi:`pytest` by yourself
   to use this command.  You can resolve these using :program:`pip`:

   .. code-block:: console

      $ pip install -e .[tests]

   It provides more rich options like :ref:`partial-testing`.


.. _test-settings:

Test settings
-------------

You can configure settings like database connection for unit testing.
These can be set using command line options of :program:`py.test`, or
environment variables.  Here's the short listing:

===================== ================================== ======================
Command Option        Environment Variable               Meaning
===================== ================================== ======================
``--database-url``    :envvar:`CLICHE_TEST_DATABASE_URL` Database URL for
                                                         testing.
                                                         SQLite 3 by default.
``--echo-sql``                                           Print all executed
                                                         queries for failed
                                                         tests.  See
                                                         :ref:`test-echo-sql`
===================== ================================== ======================


.. _partial-testing:

Partial testing
---------------

The complete test suite is slow to run.  Slow feedback loop decreases
productivity.  (You would see your Facebook timeline or chat in the IRC
to wait the long time of testing.)  To quickly test what you're workin on,
you can run only part of complete test suite.

If you set ``-k`` test will run only particular matched suites and others
get skipped.

.. code-block:: console

   $ py.test -k work_test
   $ py.test -k test_work_has_awards

The option ``--maxfail`` is useful as well, it exits after the specified
number of failures/errors.  The ``-x`` option is equivalent to ``--maxfail=1``,
it exits instantly on the first failure/error.

.. seealso::

   `Excluding tests with py.test 2.3.4 using -k selection`__
      Since :pypi:`pytest` version 2.3.4, the ``-k`` keyword supports
      expressions.

   __ http://archlinux.me/dusty/2013/02/09/excluding-tests-with-py-test-2-3-4-using-k-selection/


.. _test-echo-sql:

Query logging of failed tests
-----------------------------

Sometimes you would want to see logs of database queries to debug failed tests.
You can see these using ``--echo-sql`` option.

.. sourcecode:: console

   $ py.test --echo-sql
