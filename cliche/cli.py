""":mod:`cliche.cli` --- Command-line interfaces
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import logging.config
import os
import pathlib
import sys

from alembic.util import CommandError
from flask.ext.script import Manager

from .config import read_config
from .orm import downgrade_database, upgrade_database
from .web.app import app
from .web.db import get_database_engine

from .services.tvtropes.crawler import crawl as crawl_tvtropes

__all__ = ('get_database_engine', 'initialize_app', 'main', 'manager')


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


def initialize_app(config=None):
    """(:class:`flask.ext.script.Manager`) A Flask-Script manager object."""
    if config is None:
        try:
            config = os.environ['CLICHE_CONFIG']
        except KeyError:
            print('The -c/--config option or CLICHE_CONFIG environment '
                  'variable is required', file=sys.stderr)
            raise SystemExit(1)
    if not os.path.isfile(config):
        print('The configuration file', config, 'cannot be read.')
        raise SystemExit(1)
    config = read_config(filename=pathlib.Path(config))
    app.config.update(config)
    return app


manager = Manager(initialize_app)

manager.add_option('-c', '--config',
                   dest='config',
                   help='Configuration file (YAML or Python)')

#: (:class:`collections.abc.Callable`) The CLI entry point.
main = manager.run


@manager.option('revision', nargs='?', default='head',
                help='Revision upgrade/downgrade to')
def upgrade(revision):
    """Creates the database tables, or upgrade it to the latest revision."""
    logging_config = dict(ALEMBIC_LOGGING)
    logging.config.dictConfig(logging_config)
    try:
        engine = get_database_engine()
    except RuntimeError as e:
        print(e, file=sys.stderr)
    else:
        try:
            upgrade_database(engine, revision)
        except CommandError as e:
            if revision != 'head':
                try:
                    downgrade_database(engine, revision)
                except CommandError as e:
                    print(e, file=sys.stderr)
            else:
                print(e, file=sys.stderr)


@manager.command
def crawl():
    crawl_tvtropes(app.config)
    """Crawls TVTropes and saves entities into database."""


if __name__ == '__main__':
    main()
