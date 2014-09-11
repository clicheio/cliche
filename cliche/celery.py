""":mod:`cliche.celery` --- Celery_-backed task queue worker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. _Celery: http://www.celeryproject.org/

"""
import os
import pathlib

from celery import Celery, current_app, current_task
from celery.loaders.base import BaseLoader
from celery.signals import task_postrun
from sqlalchemy.engine import create_engine, Engine

from .config import ConfigDict, read_config
from .orm import Session, import_all_modules

__all__ = 'Loader', 'get_database_engine', 'get_session', 'app'


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
