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
    works = set()

    def make_work(name, media_type):
        work = Work(media_type=media_type)
        work.names.update({
            Name(
                nameable=work,
                name=name,
                locale=HashableLocale.parse('en_US')
            )
        })
        works.add(work)
        return work

    def add_trope(name):
        if not tropes.get(name):
            tropes[name] = Trope(name=name)

    def add_tropes(names):
        for name in names:
            add_trope(name)

    def get_trope(name):
        add_trope(name)
        return tropes[name]

    def get_tropes(*names):
        res = set()
        for name in names:
            res.add(get_trope(name))
        return res

    lor = make_work('The Lord of the Rings', 'Film')
    lor.tropes.update(get_tropes(
        'Come with Me If You Want to Live',
        'Friends All Along',
        'I Lied',
    ))

    commando = make_work('Commando', 'Film')
    commando.tropes.update(get_tropes(
        'Badass',
        'The Dragon',
        'I Lied',
        'One-Man Army',
    ))

    zombieland = make_work('Zombieland', 'Film')
    zombieland.tropes.update(get_tropes(
        'Action Duo',
        'Cool Car',
        'One-Man Army',
        'Zombie Infectee',
    ))

    resident_evil = make_work('Resident Evil', 'Film')
    resident_evil.tropes.update(get_tropes(
        'Action Girl',
        'Evil Elevator',
        'Take a Third Option',
        'Zombie Infectee',
    ))

    titanic = make_work('Titanic', 'Film')
    titanic.tropes.update(get_tropes(
        'Action Girl',
        'Badass',
        'The Dragon',
        'Take a Third Option',
        'MacGuffin',
    ))

    man_in_black = make_work('Men in Black', 'Film')
    man_in_black.tropes.update(get_tropes(
        'Cool Car',
        'Creator Cameo',
        'The Dog Is an Alien',
        'MacGuffin',
        'Secret Test',
    ))

    the_wizard_of_oz = make_work('The Wizard of Oz', 'Film')
    the_wizard_of_oz.tropes.update(get_tropes(
        'Adult Fear',
        'Cool Horse',
        'Kick the Dog',
        'MacGuffin',
    ))

    the_amazing_spider_man = make_work('The Amazing Spider-Man', 'Film')
    the_amazing_spider_man.tropes.update(get_tropes(
        'Adult Fear',
        'Big Eater',
        'Byronic Hero',
        'Kick the Dog',
    ))

    v_for_vendetta = make_work('V for Vendetta', 'Film')
    v_for_vendetta.tropes.update(get_tropes(
        'After the End',
        'The Faceless',
        'Byronic Hero',
        'Secret Test',
        'You Are Number Six',
    ))

    stardust = make_work('Stardust', 'Film')
    stardust.tropes.update(get_tropes(
        'Black Comedy',
        'Blue Blood: Literally',
        'Terrible Trio',
        'You Are Number Six',
    ))

    monty_pythons_the_meaning_of_life = \
        make_work("Monty Python's The Meaning of Life", 'Film')
    monty_pythons_the_meaning_of_life.tropes.update(get_tropes(
        'Badass Grandpa',
        'Black Comedy',
        'Self-Deprecation',
        'Stupid Boss',
    ))

    die_hard = make_work('Die Hard', 'Film')
    die_hard.tropes.update(get_tropes(
        'Badass Grandpa',
        'The Dragon',
        'The Driver',
        'Secret Test',
    ))

    captain_america_the_first_avenger = \
        make_work('Captain America: The First Avenger', 'Film')
    captain_america_the_first_avenger.tropes.update(get_tropes(
        'Action Girl',
        'Cool Bike',
        'Cool Boat',
        'Cool Guns',
        'Cool Helmet',
        'Cool Plane',
        'Cool Car',
        'Fake Ultimate Hero',
        'Secret Test',
    ))

    maverick = make_work('Maverick', 'Film')
    maverick.tropes.update(get_tropes(
        'Fake Ultimate Hero',
        'Friends All Along',
        'My Favorite Shirt',
        'Take My Hand',
    ))

    the_matrix = make_work('The Matrix', 'Film')
    the_matrix.tropes.update(get_tropes(
        'All Just a Dream',
        'Bullet Time',
        'Heroic Sacrifice',
        'My Favorite Shirt',
        'Take My Hand',
        'Use Your Head',
    ))

    the_terminator = make_work('The Terminator', 'Film')
    the_terminator.tropes.update(get_tropes(
        'Come with Me If You Want to Live',
        'Heroic Sacrifice',
        'Kick the Dog',
        'What Year Is This?',
    ))

    jumanji = make_work('Jumanji', 'Film')
    jumanji.tropes.update(get_tropes(
        'Adult Fear',
        'Badass',
        'Deus ex Machina',
        'Heroic Sacrifice',
        'What Year Is This?',
    ))

    independence_day = make_work('Independence Day', 'Film')
    independence_day.tropes.update(get_tropes(
        'Alien Invasion',
    ))

    naruto = make_work('Naruto', 'Anime')
    naruto.tropes.update(get_tropes(
        "LEGO Genetics",
        "Limited Wardrobe",
        "Line-of-Sight Name",
        "Living MacGuffin",
        "Living Weapon",
        "Loads and Loads of Characters",
        "Local Hangout",
        "Longest Pregnancy Ever",
        "Loophole Abuse",
        "Losing Your Head",
        "Love Hurts",
        "Love Letter",
        "Luke, I Am Your Father",
        "Mandatory Unretirement",
        "Magical Eye",
        "Magic by Any Other Name",
        "Mama Bear",
        "Man Behind the Man",
        "Manly Tears",
        "Master-Apprentice Chain",
        "Me's a Crowd",
        "Meaningful Funeral",
        "Meaningful Name",
        "Mentor Occupational Hazard",
        "Messianic Archetype",
        "Meteor Move",
        "Mind Rape",
        "Mind Screw",
        "Misery Builds Character",
        "Monster Shaped Mountain",
        "Multiple-Tailed Beast",
        "Mundane Utility",
        "My God, What Have I Done?",
        "Never a Self-Made Woman",
        "New Powers as the Plot Demands",
        "Nice Job Breaking It, Hero",
        "Nice Job Fixing It, Villain",
        "Ninja",
        "Ninja Log",
        "Nobody Poops",
        "Nonhumans Lack Attributes",
        "The Nose Bleed",
        "Not a Date / She Is Not My Girlfriend",
        "Not Cheating Unless You Get Caught",
        "Not Even Human",
        "Nothing but Skin and Bones",
        "Not Just a Tournament",
        "Not Quite Dead",
        "Not So Different",
        "Not So Stoic",
        "Nothing Is the Same Anymore",
        "Oblivious Mockery",
        "Oddly Small Organization",
        "Official Couple",
        "Offscreen Moment of Awesome",
        "Oh, Crap",
        "One Extra Member",
        "One-Winged Angel",
        "Only a Flesh Wound",
        "The Only One Allowed to Defeat You",
        "Organ Theft",
        "Orphanage of Love",
        "Our Zombies Are Different",
        "Out of Focus",
        "Overshadowed by Awesome",
        "Papa Wolf",
        "Parental Abandonment",
        "Passion Is Evil",
        "Person of Mass Destruction",
        "Phlebotinum-Handling Requirements",
        "The Pirates Who Don't Do Anything",
        "Playing with Fire",
        "Please Don't Leave Me",
        "Plot Armor",
        "The Plot Reaper",
        "Plot Tumor",
        "Police Are Useless",
        "Power Makes Your Hair Grow",
        "The Power of Friendship",
        "The Power of Hate",
        "The Power of Love",
        "Powers as Programs",
        "Protagonist-Centered Morality",
        "Protagonist Journey to Villain",
        "Psycho Rangers",
        "A Pupil of Mine Until He Turned to Evil",
        "Punny Name",
        "Random Power Ranking",
        "Rank Up",
        "Rays from Heaven",
        "Razor Sharp Hand",
        "Reality Ensues",
        "Reality Is Unrealistic",
        "Reality Warper",
        "Recruited From The Gutter",
        "Redemption Equals Death",
        "Red Oni, Blue Oni",
        "Refuge in Audacity",
        "Red Shirt Army",
        "Red String of Fate",
        "Reformed But Not Tamed",
        "Reptiles Are Abhorrent",
        "Rescue Romance",
        "The Rest Shall Pass",
        "Retcon",
        "Reusable Lighter Toss",
        "The Reveal",
        "Right Makes Might",
        "Roofhopping",
        "Rousing Speech",
        "Rousseau Was Right",
        "Rule of Symbolism",
        "Rummage Sale Reject",
        "Running Gagged",
        "Sacrificial Revival Spell",
        "Sadistic Choice",
        "Sarutobi Sasuke",
        "Save The World Climax",
        "Saving the Orphanage",
        "Say My Name",
        "School Saved My Life",
        "Schizo Tech",
        "Sci Fi Fantasy Writers Have No Sense Of Scale",
        "Sealed Evil in a Can",
        "Self-Duplication",
        "Self Healing Phlebotinum",
        "Sempai/Kohai",
        "Series Continuity Error",
        "Serpent of Immortality",
        "Sexposition",
        "Shared Family Quirks",
        "Ship Sinking",
        "Ship Tease",
        "Shoo Out the Clowns",
        "Shout-Out",
        "Shoot the Dog",
        "Shoot the Hostage",
        "Shown Their Work",
        "Shut Up, Hannibal!",
        "Sins of Our Fathers",
        "Skeleton Government",
        "Skyscraper City",
        "Slap Yourself Awake",
        "Slave Brand",
        "Smash The Symbol",
        "Smitten Teenage Girl",
        "The Smurfette Principle",
        "Snap to the Side",
        "Sneezing",
        "Social Services Does Not Exist",
        "Sorting Algorithm of Evil",
        "The Spartan Way",
        "Spell Levels",
        "Spiritual Successor",
        "Spoiler",
        "Spot the Imposter",
        "Spy Catsuit",
        "Standard Evil Organization Squad",
        "Start of Darkness",
        "Start X to Stop X",
        "Step into the Blinding Fight",
        "Stock Ninja Weaponry",
        "Summon Magic",
        "Super-Powered Evil Side",
        "Super Reflexes",
        "Supernatural Martial Arts",
        "Superpowerful Genetics",
        "Take a Third Option",
        "Take Over the World",
        "Take That, Audience!",
        "Taking the Bullet",
        "Talk to the Fist",
        "Talking Is a Free Action",
        "Talking the Monster to Death",
        "Tears of Joy",
        "Teen Genius",
        "Tempting Fate",
        "That's No Moon!",
        "There Are No Therapists",
        "There Is No Kill Like Overkill",
        "This Is Something He's Got to Do Himself",
        "Those Two Guys",
        "Throwing the Fight",
        "Tickle Torture",
        "Tiger Versus Dragon",
        "Time Skip",
        "To Be a Master",
        "Took a Level in Badass",
        "Tournament Arc",
        "Trail of Bread Crumbs",
        "Training The Gift Of Magic",
        "Training the Peaceful Villagers",
        "Trash Talk",
        "Traumatic Superpower Awakening",
        "Triang Relations",
        "Troll",
        "True Companions",
        "Try Not to Die",
        "Tsundere",
        "Tunnel King",
        "Turtle Island",
        "Two Guys and a Girl",
        "Two Scenes, One Dialogue",
        "Unrequited Love Switcheroo",
        "Unstoppable Rage",
        "Unwitting Instigator of Doom",
        "Used to Be a Sweet Kid",
        "Utopia Justifies the Means",
        "Vein-O-Vision",
        "Vengeance Feels Empty",
        "Vicious Cycle",
        "Viewers Are Goldfish",
        "Villain Override",
        "Vomit Indiscretion Shot",
        "Walk on Water",
        "War Arc",
        "The War to End All Wars",
        "Warrior Therapist",
        "Wave Motion Gun",
        "Way Past the Expiration Date",
        "Weapon Tombstone",
        "Welcome Back, Traitor",
        "Well-Intentioned Extremist",
        "Wham Episode",
        "Wham Line",
        "Wham Shot",
        "What Happened to the Mouse?",
        "What the Hell, Hero?",
        "When All You Have Is a Hammer",
        "Willfully Weak",
        "Women in Refrigerators",
        "Woobie, Destroyer of Worlds",
        "The Worf Barrage",
        "The Worf Effect",
        "Worf Had the Flu",
        "World Domination",
        "World Half Full",
        "World of Badass",
        "World Of Card Board Speech",
        "World of Ham",
        "World of Silence",
        "Would Hit a Girl",
        "Wrap It Up",
        "X-Ray Vision",
        "Yoyo Plot Point",
        "You Are Already Dead",
        "You Are Not Alone",
        "You Know The One",
        "Your Mind Makes It Real",
    ))

    with flask_app.app_context():
        engine = get_database_engine()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        with session.begin():
            session.add_all(works)


#: (:class:`collections.abc.Callable`) The CLI entry point.
main = cli
