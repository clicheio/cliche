""":mod:`cliche.cli` --- Command-line interfaces
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import code
import functools
import logging.config
import os
import pathlib
import sys

from alembic.util import CommandError
from click import Path, argument, echo, group, option
from flask import _request_ctx_stack
from sassutils.wsgi import SassMiddleware
from werkzeug.utils import import_string

from .celery import app as celery_app
from .config import read_config
from .name import Name
from .orm import Base, downgrade_database, upgrade_database
from .sqltypes import HashableLocale
from .web.app import (app as flask_app,
                      setup_sentry as flask_setup_sentry)
from .web.db import get_database_engine, session
from .work import Trope, Work


__all__ = ('initialize_app', 'config', 'main')

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


def config(func):
    """Provide :option:`--config` or :option:`-c` option and
    run :func:`initialize_app()` automatically.

    :param func: a command function to decorate
    :type func: :class:`collections.abc.Callable`
    :returns: decorated ``func``

    """
    @functools.wraps(func)
    def internal(*args, **kwargs):
        initialize_app(kwargs.pop('config'))
        func(*args, **kwargs)

    deco = option('--config', '-c', type=Path(exists=True),
                  help='Configuration file (YAML or Python)')
    return deco(internal)


def initialize_app(config=None):
    """Initialize celery/flask app.

    :param config: a config file path. accept :file:`.py`, :file:`.yml` file.
                   default value is :const:`None`

    """
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


@group()
def cli():
    """cliche for integrated command for cliche.io service."""


@cli.command()
@argument('revision', default='head')
@config
def upgrade(revision):
    """Create the database tables, or upgrade it to the latest revision."""

    logging_config = dict(ALEMBIC_LOGGING)
    logging.config.dictConfig(logging_config)
    with flask_app.app_context():
        engine = get_database_engine()
        try:
            upgrade_database(engine, revision)
        except CommandError as e:
            if revision != 'head':
                try:
                    downgrade_database(engine, revision)
                except CommandError as e:
                    echo(e, file=sys.stderr)
                    raise SystemExit(1)
            else:
                echo(e, file=sys.stderr)
                raise SystemExit(1)


@cli.command()
@argument('service')
@config
def sync(service):  # FIXME available service listing
    """Sync to services."""
    try:
        sync = import_string('cliche.services.' + service + ':sync')
    except ImportError:
        echo('There is no such service \'{}\' suitable for synchronization.'
             .format(service),
             file=sys.stderr)
    else:
        sync.delay()


@cli.command()
@config
def shell():
    """Run a Python shell inside Flask application context."""
    with flask_app.test_request_context():
        context = dict(app=_request_ctx_stack.top.app)

        # Use basic python shell
        code.interact(local=context)


@cli.command()
@option('--host', '-h')
@option('--port', '-p', type=int)
@option('--threaded', is_flag=True)
@option('--processes', type=int, default=1)
@option('--passthrough-errors', is_flag=True)
@option('--debug/--no-debug', '-d/-D', default=None,
        help='enable the Werkzeug debugger'
             ' (DO NOT use in production code)')
@option('--reload/--no-reload', '-r/-R', default=None,
        help='monitor Python files for changes'
             ' (not 100% safe for production use)')
@config
def runserver(host, port, threaded, processes,
              passthrough_errors, debug, reload):
    """Run the Flask development server i.e. app.run()"""

    if flask_app.debug:
        # scss compile automatically in debug mode
        flask_app.wsgi_app = SassMiddleware(flask_app.wsgi_app, {
            'cliche.web': ('static/sass', 'static/css', '/static/css')
        })

    if debug is None:
        debug = flask_app.debug
    if reload is None:
        reload = flask_app.debug

    flask_setup_sentry()

    flask_app.run(host=host,
                  port=port,
                  debug=debug,
                  use_debugger=debug,
                  use_reloader=reload,
                  threaded=threaded,
                  processes=processes,
                  passthrough_errors=passthrough_errors)


@cli.command()
@config
def dummy():
    """Generate dummy data for test."""
    def make_film(name):
        film = Work(media_type='Film')
        film.names.update({
            Name(
                nameable=film,
                name=name,
                locale=HashableLocale.parse('en_US')
            )
        })
        return film

    action_duo = Trope(name='Action Duo')
    action_girl = Trope(name='Action Girl')
    adult_fear = Trope(name='Adult Fear')
    badass = Trope(name='Badass')
    come_with_me = Trope(name='Come with Me If You Want to Live')
    cool_car = Trope(name='Cool Car')
    cool_horse = Trope(name='Cool Horse')
    creater_cameo = Trope(name='Creator Cameo')
    the_dog_is_an_alien = Trope(name='The Dog Is an Alien')
    the_dragon = Trope(name='The Dragon')
    evil_elevator = Trope(name='Evil Elevator')
    friends_all_along = Trope(name='Friends All Along')
    i_lied = Trope(name='I Lied')
    kick_the_dog = Trope(name='Kick the Dog')
    macguffin = Trope(name='MacGuffin')
    one_man_army = Trope(name='One-Man Army')
    take_a_third_option = Trope(name='Take a Third Option')
    zombie_infectee = Trope(name='Zombie Infectee')

    lor = make_film('The Lord of the Rings')
    lor.tropes.update({
        action_girl,
        come_with_me,
        friends_all_along,
        i_lied
    })

    commando = make_film('Commando')
    commando.tropes.update({
        badass,
        the_dragon,
        i_lied,
        one_man_army
    })

    zombieland = make_film('Zombieland')
    zombieland.tropes.update({
        action_duo,
        cool_car,
        one_man_army,
        zombie_infectee
    })

    resident_evil = make_film('Resident Evil')
    resident_evil.tropes.update({
        action_girl,
        evil_elevator,
        take_a_third_option,
        zombie_infectee
    })

    titanic = make_film('Titanic')
    titanic.tropes.update({
        action_girl,
        badass,
        the_dragon,
        take_a_third_option,
        macguffin
    })

    man_in_black = make_film('Men in Black')
    man_in_black.tropes.update({
        cool_car,
        creater_cameo,
        the_dog_is_an_alien,
        macguffin
    })

    the_wizard_of_oz = make_film('The Wizard of Oz')
    the_wizard_of_oz.tropes.update({
        adult_fear,
        cool_horse,
        kick_the_dog,
        macguffin
    })

    with flask_app.app_context():
        engine = get_database_engine()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        with session.begin():
            session.add_all([
                lor,
                commando,
                zombieland,
                resident_evil,
                titanic,
                man_in_black,
                the_wizard_of_oz
            ])


#: (:class:`collections.abc.Callable`) The CLI entry point.
main = cli
