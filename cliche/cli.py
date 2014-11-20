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
from .services.align import alignment


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
def align():
    """Align database"""
    alignment()


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

    tropes = dict()

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

    def add_trope(name):
        if not tropes.get(name):
            tropes[name] = Trope(name=name)

    def add_tropes(names):
        for name in names:
            add_trope(name)

    def get_trope(name):
        return tropes.get(name)

    def get_tropes(names):
        for name in names:
            if name:
                yield name

    add_tropes(
        'Accidental Kidnapping',
        'Action Duo',
        'Action Girl',
        'Adult Fear',
        'After the End',
        'Alien Invasion',
        'All Just a Dream',
        'Badass',
        'Badass Grandpa',
        'Big Eater',
        'Black Comedy',
        'Blue Blood: Literally',
        'Bullet Time',
        'Byronic Hero',
        'Come with Me If You Want to Live',
        'Cool Bike',
        'Cool Boat',
        'Cool Car',
        'Cool Guns',
        'Cool Helmet',
        'Cool Plane',
        'Cool Horse',
        'Creator Cameo',
        'Deus ex Machina',
        'Dressing as the Enemy',
        'The Dog Is an Alien',
        'The Dragon',
        'The Driver',
        'Evil Elevator',
        'The Faceless',
        'Fake Ultimate Hero',
        'Friends All Along',
        'Great Escape',
        'Heroic Sacrifice',
        'I Lied',
        'Kick the Dog',
        'Love-Obstructing Parents',
        'MacGuffin',
        'My Favorite Shirt',
        'Not Blood Siblings',
        'Not Evil, Just Misunderstood',
        'Not Quite Dead',
        'One-Man Army',
        'Secret Test',
        'Self-Deprecation',
        'Stupid Boss',
        'Take a Third Option',
        'Take My Hand',
        'Terrible Trio',
        'Use Your Head',
        'What Year Is This?',
        'You Are Number Six',
        'Zombie Infectee',
    )

    lor = make_film('The Lord of the Rings')
    lor.tropes.update(get_tropes({
        'Come with Me If You Want to Live',
        'Friends All Along',
        'I Lied',
    }))

    commando = make_film('Commando')
    commando.tropes.update(get_tropes({
        'Badass',
        'The Dragon',
        'I Lied',
        'One-Man Army',
    }))

    zombieland = make_film('Zombieland')
    zombieland.tropes.update(get_tropes({
        'Action Duo',
        'Cool Car',
        'One-Man Army',
        'Zombie Infectee',
    }))

    resident_evil = make_film('Resident Evil')
    resident_evil.tropes.update(get_tropes({
        'Action Girl',
        'Evil Elevator',
        'Take a Third Option',
        'Zombie Infectee',
    }))

    titanic = make_film('Titanic')
    titanic.tropes.update(get_tropes({
        'Action Girl',
        'Badass',
        'The Dragon',
        'Take a Third Option',
        'MacGuffin',
    }))

    man_in_black = make_film('Men in Black')
    man_in_black.tropes.update(get_tropes({
        'Cool Car',
        'Creator Cameo',
        'The Dog Is an Alien',
        'MacGuffin',
        'Secret Test',
    }))

    the_wizard_of_oz = make_film('The Wizard of Oz')
    the_wizard_of_oz.tropes.update(get_tropes({
        'Adult Fear',
        'Cool Horse',
        'Kick the Dog',
        'MacGuffin',
    }))

    the_amazing_spider_man = make_film('The Amazing Spider-Man')
    the_amazing_spider_man.tropes.update(get_tropes({
        'Adult Fear',
        'Big Eater',
        'Byronic Hero',
        'Kick the Dog',
    }))

    v_for_vendetta = make_film('V for Vendetta')
    v_for_vendetta.tropes.update(get_tropes({
        'After the End',
        'The Faceless',
        'Byronic Hero',
        'Secret Test',
        'You Are Number Six',
    }))

    stardust = make_film('Stardust')
    stardust.tropes.update(get_tropes({
        'Black Comedy',
        'Blue Blood: Literally',
        'Terrible Trio',
        'You Are Number Six',
    }))

    monty_pythons_the_meaning_of_life = \
        make_film("Monty Python's The Meaning of Life")
    monty_pythons_the_meaning_of_life.tropes.update(get_tropes({
        'Badass Grandpa',
        'Black Comedy',
        'Self-Deprecation',
        'Stupid Boss',
    }))

    die_hard = make_film('Die Hard')
    die_hard.tropes.update(get_tropes({
        'Badass Grandpa',
        'The Dragon',
        'The Driver',
        'Secret Test',
    }))

    captain_america_the_first_avenger = \
        make_film('Captain America: The First Avenger')
    captain_america_the_first_avenger.tropes.update(get_tropes({
        'Action Girl',
        'Cool Bike',
        'Cool Boat',
        'Cool Guns',
        'Cool Helmet',
        'Cool Plane',
        'Cool Car',
        'Fake Ultimate Hero',
        'Secret Test',
    }))

    maverick = make_film('Maverick')
    maverick.tropes.update(get_tropes({
        'Fake Ultimate Hero',
        'Friends All Along',
        'My Favorite Shirt',
        'Take My Hand',
    }))

    the_matrix = make_film('The Matrix')
    the_matrix.tropes.update(get_tropes({
        'All Just a Dream',
        'Bullet Time',
        'Heroic Sacrifice',
        'My Favorite Shirt',
        'Take My Hand',
        'Use Your Head',
    }))

    the_terminator = make_film('The Terminator')
    the_terminator.tropes.update(get_tropes({
        'Come with Me If You Want to Live',
        'Heroic Sacrifice',
        'Kick the Dog',
        'What Year Is This?',
    }))

    jumanji = make_film('Jumanji')
    jumanji.tropes.update(get_tropes({
        'Adult Fear',
        'Badass',
        'Deus ex Machina',
        'Heroic Sacrifice',
        'What Year Is This?',
    }))

    independence_day = make_film('Independence Day')
    independence_day.tropes.update(get_tropes({
        'Alien Invasion',
    }))

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
                the_wizard_of_oz,
                the_amazing_spider_man,
                v_for_vendetta,
                stardust,
                monty_pythons_the_meaning_of_life,
                die_hard,
                captain_america_the_first_avenger,
                maverick,
                the_matrix,
                the_terminator,
                jumanji,
            ])


#: (:class:`collections.abc.Callable`) The CLI entry point.
main = cli
