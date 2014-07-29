""":mod:`cliche.cli` --- Command-line interfaces
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:envvar:`CLICHE_DATABASE_URL`
   The URL of the database to use.

   .. seealso::

      SQLAlchemy --- :ref:`database_urls`
         The URL is passed to SQLAlchemy's :func:`~sqlalchemy.create_engine()`
         function.

"""
import argparse
import logging.config
import os

from alembic.util import CommandError
from sqlalchemy.engine import create_engine

from .orm import downgrade_database, upgrade_database

__all__ = {'get_database_engine', 'migrate'}


ALEMBIC_LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'level': 'NOTSET',
            'class': 'logging.StreamHandler',
            'formatter': 'generic'
        }
    },
    'formatters': {
        'generic': {
            'format': '%(levelname)-5.5s [%(name)s] %(message)s',
            'datefmt': '%H:%M:%S'
        }
    },
    'root': {
        'level': 'WARN',
        'handlers': ['console']
    },
    'loggers': {
        'alembic': {
            'level': 'INFO',
            'handlers': []
        },
        'sqlalchemy.engine': {
            'level': 'WARN',
            'handlers': []
        }
    }
}



def get_database_engine():
    """Read the configuration (environment variables) and then return
    an engine to database.

    :returns: the database engine
    :rtype: :class:`sqlalchemy.engine.base.Engine`
    :raises RuntimeError: when the configuration (environment variables) isn't
                          properly set

    """
    try:
        url = os.environ['CLICHE_DATABASE_URL']
    except KeyError:
        raise RuntimeError('Missing CLICHE_DATABASE_URL environment '
                           'variable')
    return create_engine(url)


def migrate(args=None):
    """Creates the database tables, or upgrade it to the latest revision."""
    parser = argparse.ArgumentParser(description=migrate.__doc__)
    parser.add_argument('revision', nargs='?', default='head',
                        help='Revision upgrade/downgrade to')
    args = parser.parse_args(args)
    logging_config = dict(ALEMBIC_LOGGING)
    logging.config.dictConfig(logging_config)
    try:
        engine = get_database_engine()
    except RuntimeError as e:
        parser.error(str(e))
    else:
        try:
            upgrade_database(engine, args.revision)
        except CommandError as e:
            if args.revision != 'head':
                try:
                    downgrade_database(engine, args.revision)
                except CommandError as e:
                    parser.error(str(e))
            else:
                parser.error(str(e))
