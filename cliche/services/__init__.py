""":mod:`cliche.services` --- Interfacing external services
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

How to add a new external service
---------------------------------

In order to add a new service to cliche, you must create a subpackage under
:data:`cliche.services` and expose some methods referring to interfaces,
using :file:`__init__.py`.

Interfaces needed to be exposed
-------------------------------

- :func:`sync()`: Method to delay a main crawling task to the queue. It should
  be decorated with :code:`@app.task` to be defined as a celery app worker
  task. It should have no arguments and no return. Every output should be made
  as a log to celery logger.

Example :file:`__init__.py`
---------------------------

.. sourcecode:: python

   from .crawler import crawl as sync  # noqa


   __all__ = 'sync',

Note that you will need the import lines annotated with :code:`# noqa` because
otherwise :program:`flake8` will consider it as unused import.

"""
