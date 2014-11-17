""":mod:`cliche.celery` --- Celery_-backed task queue worker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes web app should provide time-consuming features that cannot
immediately respond to user (and we define "immediately" as "shorter than
a second or two seconds" in here).  Such things should be queued and then
processed by background workers.  Celery_ does that in natural way.

We use this at serveral points like resampling images to make thumbnails,
or crawling ontology data from other services.  Such tasks are definitely
cannot "immediately" respond.

.. seealso::

   :ref:`faq-when-to-use` --- Celery FAQ
      Answer to what kinds of benefits are there in Celery.

   `Queue everything and delight everyone`__
      This article describes why you should use a queue in a web application.

   __ http://decafbad.com/blog/2008/07/04/queue-everything-and-delight-everyone

.. _Celery: http://celeryproject.org/


How to define tasks
-------------------

In order to defer some types of tasks, you have to make these functions
a task.  It's not a big deal, just attach a decorator to them::

    @celery.task(ignore_result=True)
    def do_heavy_work(some, inputs):
        '''Do something heavy work.'''
        ...


How to defer tasks
------------------

It's similar to ordinary function calls except it uses :meth:`delay()
<celery.app.task.Task.delay>` method (or :meth:`apply_async()
<celery.app.task.Task.apply_async>` method) instead of calling operator::

    do_heavy_work.delay('some', inputs='...')

That command will be queued and sent to one of distributed workers.
That means these argument values are serialized using :mod:`json`.
If any argument value isn't serializable it will error.
Simple objects like numbers, strings, tuples, lists, dictionaries are
safe to serialize.
In the other hand, entity objects (that an instance of :class:`cliche.orm.Base`
and its subtypes) mostly fail to serialize, so use primary key values like
entity id instead of object itself.


What things are ready for task?
-------------------------------

Every deferred call of task share equivalent inital state:

- You can get a database session using :func:`get_session()`.
- You also can get a database engine using :func:`get_database_engine()`.

While there are several things not ready either:

- Flask's request context isn't ready for each task.  You should explicitly
  deal with it using :meth:`~flask.Flask.request_context()` method
  to use context locals like :class:`flask.request`.
  See also :ref:`request-context`.
- Physical computers would differ from web environment.  Total memory,
  CPU capacity, the number of processors, IP address, operating system,
  Python VM (which of PyPy or CPython), and other many environments also
  can vary.  Assume nothing on these variables.
- Hence global states (e.g. module-level global variables) are completely
  isolated from web environment which called the task.  Don't depend on
  such global states.


How to run Celery worker
------------------------

:program:`celery worker` (formerly :program:`celeryd`) takes Celery app object
as its endpoint, and Cliche's endpoint is :data:`cliche.celery.celery`.
You can omit the latter variable name and module name: :mod:`cliche`.
Execute the following command in the shell:

.. sourcecode:: console

   $ celery worker -A cliche --config dev.cfg.yml
    -------------- celery@localhost v3.1.13 (Cipater)
   ---- **** -----
   --- * ***  * -- Darwin-13.3.0-x86_64-i386-64bit
   -- * - **** ---
   - ** ---------- [config]
   - ** ---------- .> app:         cliche.celery:0x1... (cliche.celery.Loader)
   - ** ---------- .> transport:   redis://localhost:6379/5
   - ** ---------- .> results:     disabled
   - *** --- * --- .> concurrency: 4 (prefork)
   -- ******* ----
   --- ***** ----- [queues]
    -------------- .> celery           exchange=celery(direct) key=celery


   [2014-09-12 00:31:25,150: WARNING/MainProcess] celery@localhost ready.

Note that you should pass the same configuration file (``--config`` option)
to the WSGI application.  It should contain ``DATABASE_URL`` and so on.


References
----------

"""
import os
import pathlib

from celery import Celery, current_app, current_task
from celery.loaders.base import BaseLoader
from celery.signals import celeryd_init, task_postrun
from raven import Client
from raven.conf import setup_logging
from raven.handlers.logging import SentryHandler
from sqlalchemy.engine import create_engine, Engine

from .config import ConfigDict, read_config
from .orm import Session, import_all_modules

__all__ = (
    'Loader',
    'get_database_engine',
    'get_session',
    'get_raven_client',
    'app',
)


app = Celery(__name__, loader=__name__ + ':Loader')


class Loader(BaseLoader):
    """The loader used by Cliche app."""

    def read_configuration(self):
        config = ConfigDict()
        config_path = os.environ.get(
            'CELERY_CONFIG_MODULE',
            os.environ.get('CLICHE_CONFIG')
        )
        if config_path is not None:
            config = read_config(pathlib.Path(config_path))
        config['CELERY_IMPORTS'] = import_all_modules()
        config['CELERY_ACCEPT_CONTENT'] = ['pickle', 'json']
        return config


def get_database_engine() -> Engine:
    """Get a database engine.

    :returns: a database engine
    :rtype: :class:`sqlalchemy.engine.base.Engine`

    """
    config = current_app.conf
    if 'DATABASE_ENGINE' not in config:
        db_url = config['DATABASE_URL']
        config['DATABASE_ENGINE'] = create_engine(db_url)
        if 'BROKER_URL' not in config:
            config['BROKER_URL'] = 'sqla+' + db_url
        if 'CELERY_RESULT_BACKEND' not in config and \
                'CELERY_RESULT_DBURI' not in config:
            config['CELERY_RESULT_BACKEND'] = 'database'
            config['CELERY_RESULT_DBURI'] = db_url
    return config['DATABASE_ENGINE']


def get_session() -> Session:
    """Get a database session.

    :returns: a database session
    :rtype: :class:`~.orm.Session`

    """
    task = current_task._get_current_object()
    request = task.request
    if getattr(request, 'db_session', None) is None:
        request.db_session = Session(bind=get_database_engine())
    return request.db_session


@task_postrun.connect
def close_session(task_id, task, *args, **kwargs):
    """Close the session if there's the opened session."""
    session = getattr(task.request, 'db_session', None)
    if session is not None:
        session.close()


def get_raven_client() -> Client:
    """Get a raven client.

    :returns: a raven client
    :rtype: :class:`raven.Client`

    """
    config = current_app.conf
    if 'SENTRY_DSN' in config:
        if 'RAVEN_CLIENT' not in config:
            sentry_dsn = config['SENTRY_DSN']
            config['RAVEN_CLIENT'] = Client(
                dsn=sentry_dsn,
                include_paths=[
                    'cliche',
                ],
            )
        return config['RAVEN_CLIENT']
    else:
        return None


@celeryd_init.connect
def setup_raven_logging(conf=None, **kwargs):
    client = get_raven_client()
    if client is not None:
        handler = SentryHandler(client)
        setup_logging(handler)


@task_failure.connect
def report_task_failure(task_id, exception, args, kwargs, traceback, einfo):
    client = get_raven_client()
    client.captureException(einfo.exc_info)
