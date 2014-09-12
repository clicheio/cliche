""":mod:`cliche.cli` --- Command-line interfaces
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import code
import logging.config
import os
import pathlib
import sys

from alembic.util import CommandError
from click import Path, argument, echo, group, option
from flask import _request_ctx_stack

from .celery import app as celery_app
from .config import read_config
from .orm import downgrade_database, upgrade_database
from .web.app import app as flask_app
from .web.db import get_database_engine

from .services.tvtropes.crawler import crawl as crawl_tvtropes

__all__ = ('get_database_engine', 'initialize_app', 'main')


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
    flask_app.config.update(config)
    celery_app.conf.update(config)
    return flask_app


@group()
def cli():
    '''cliche for intergrated command for cliche.io service.'''
    pass


@cli.command()
@option('--config', '-c', type=Path(exists=True),
        help='Configuration file (YAML or Python)')
@argument('revision', default='head') # help='Revision upgrade/downgrade to'
def upgrade(config, revision):
    """Creates the database tables, or upgrade it to the latest revision."""
    initialize_app(config)

    logging_config = dict(ALEMBIC_LOGGING)
    logging.config.dictConfig(logging_config)
    try:
        engine = get_database_engine()
    except RuntimeError as e:
        echo(e, file=sys.stderr)
    else:
        try:
            upgrade_database(engine, revision)
        except CommandError as e:
            if revision != 'head':
                try:
                    downgrade_database(engine, revision)
                except CommandError as e:
                    echo(e, file=sys.stderr)
            else:
                echo(e, file=sys.stderr)


@cli.command()
@option('--config', '-c', type=Path(exists=True),
        help='Configuration file (YAML or Python)')
def crawl(config):
    '''Crawles TVTropes and saves entities into database.'''
    initialize_app(config)
    crawl_tvtropes(app.config)


@cli.command()
@option('--config', '-c', type=Path(exists=True),
        help='Configuration file (YAML or Python)')
@option('--no-ipython', help='Do not use the IPython shell',
        is_flag=True)
@option('--no-bpython', help='Do not use the BPython shell',
        is_flag=True)
def shell(config, no_ipython, no_bpython):
    '''Runs a Python shell inside Flask application context.'''
    initialize_app(config)
    with app.test_request_context():
        context = dict(app=_request_ctx_stack.top.app)

        if not no_bpython:
            # Try BPython
            try:
                from bpython import embed
                embed(locals_=context)
                return
            except ImportError:
                pass
        if not no_ipython:
            # Try IPython
            try:
                try:
                    # 0.10.x
                    from IPython.Shell import IPShellEmbed
                    ipshell = IPShellEmbed()
                    ipshell(global_ns=dict(), local_ns=context)
                except ImportError:
                    # 0.12+
                    from IPython import embed
                    embed(user_ns=context)
                    return
            except ImportError:
                pass
        # Use basic python shell
        code.interact(local=context)


@cli.command()
@option('--config', '-c', type=Path(exists=True),
        help='Configuration file (YAML or Python)')
@option('--host', '-h')
@option('--port', '-p', type=int)
@option('--threaded', is_flag=True)
@option('--processes', type=int, default=1)
@option('--passthrough-errors', is_flag=True)
@option('--debug/--no-debug', '-d/-D', default=False,
        help='enable the Werkzeug debugger (DO NOT use in production code)')
@option('--reload/--no-reload', '-r/-R', default=False,
        help='monitor Python files for changes (not 100% safe for production use)')
def runserver(config, host, port, threaded, processes, passthrough_errors, debug, reload):
    '''Runs the Flask development server i.e. app.run()'''
    initialize_app(config)
    app.run(host=host,
            port=port,
            debug=debug,
            use_debugger=debug,
            use_reloader=reload,
            threaded=threaded,
            processes=processes,
            passthrough_errors=passthrough_errors)


#: (:class:`collections.abc.Callable`) The CLI entry point.
main = cli

if __name__ == '__main__':
    main()
