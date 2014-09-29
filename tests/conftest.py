import datetime
import os
import pathlib
import types

from click.testing import CliRunner
from pytest import fixture, yield_fixture
from yaml import dump

from cliche.celery import app as celery_app
from cliche.people import Person, Team
from cliche.web.app import app
from cliche.work import Credit, Franchise, Genre, Role, Title, Work, World

from .db import DEFAULT_DATABASE_URL, get_session


def pytest_addoption(parser):
    env = os.environ.get
    parser.addoption('--database-url', type='string',
                     default=env('CLICHE_TEST_DATABASE_URL',
                                 DEFAULT_DATABASE_URL),
                     help='Database URL for testing.'
                          '[default: %default]')
    parser.addoption('--echo-sql', action='store_true', default=False,
                     help='Print all executed queries for failed tests')


@fixture
def fx_tmpdir(tmpdir):
    """Equivalent to pytest-builtin ``tmpdir`` fixture except it provides
    a path as pathlib.Path, instead of py.path.local.

    """
    return pathlib.Path(str(tmpdir))


@yield_fixture
def fx_session(request):
    try:
        database_url = request.config.getoption('--database-url')
    except ValueError:
        database_url = None
    try:
        echo_sql = request.config.getoption('--echo-sql')
    except ValueError:
        echo_sql = False
    with get_session(database_url=database_url, echo_sql=echo_sql) as session:
        yield session


class FixtureModule(types.ModuleType):

    def __add__(self, module):
        clone = type(self)(self.__name__, self.__doc__)
        clone += self
        clone += module
        return clone

    def __iadd__(self, module):
        for name in dir(module):
            if not name.startswith('_'):
                setattr(self, name, getattr(module, name))
        return self


@fixture
def fx_people(fx_session):
    """create people: four artists and Peter Jackson"""
    f = FixtureModule('fx_people')

    # create four artists of 'CLAMP' team
    f.clamp_member_1 = Person(name='Nanase Ohkawa',
                              dob=datetime.date(1967, 5, 2))
    fx_session.add(f.clamp_member_1)
    f.clamp_member_2 = Person(name='Mokona',
                              dob=datetime.date(1968, 6, 16))
    fx_session.add(f.clamp_member_2)
    f.clamp_member_3 = Person(name='Tsubaki Nekoi',
                              dob=datetime.date(1969, 1, 21))
    fx_session.add(f.clamp_member_3)
    f.clamp_member_4 = Person(name='Satsuki Igarashi',
                              dob=datetime.date(1969, 2, 8))
    fx_session.add(f.clamp_member_4)

    # create 'Peter Jackson'
    f.peter_jackson = Person(name='Peter Jackson',
                             dob=datetime.date(1961, 10, 31))
    fx_session.add(f.peter_jackson)

    fx_session.flush()
    return f


@fixture
def fx_teams(fx_session, fx_people):
    """create teams: CLAMP which consists of the four artists"""
    f = FixtureModule('fx_teams')
    f += fx_people

    # create 'CLAMP' team
    f.clamp = Team(name='CLAMP')
    f.clamp.members.update({fx_people.clamp_member_1,
                            fx_people.clamp_member_2,
                            fx_people.clamp_member_3,
                            fx_people.clamp_member_4})
    fx_session.add(f.clamp)

    fx_session.flush()
    return f


@fixture
def fx_genres(fx_session):
    """create genres: Comic and Romance"""
    f = FixtureModule('fx_genres')
    f.session = fx_session

    # create 'Comic' genre
    f.comic = Genre(name='Comic')
    fx_session.add(f.comic)

    # create 'Romance' genre
    f.romance = Genre(name='Romance')
    fx_session.add(f.romance)
    fx_session.flush()
    return f


@fixture
def fx_worlds(fx_session):
    """create worlds: *Middle-earth* and *Marvel Cinematic Universe*."""
    f = FixtureModule('fx_worlds')
    f.session = fx_session

    # create fictional universe, 'Middle-earth'
    f.middle_earth = World(name='Middle-earth')
    fx_session.add(f.middle_earth)

    # create 'Marvel Cinematic Universe'
    f.marvel_universe = World(name='Marvel Cinematic Universe')
    fx_session.add(f.marvel_universe)

    fx_session.flush()
    return f


@fixture
def fx_franchises(fx_session, fx_worlds):
    """create franchises: *The Lord of the Rings*
    which belongs to *Middle-earth*, and four franchises
    which belong to *Marvel Cinematic Universe*
    """
    f = FixtureModule('fx_franchises')
    f.session = fx_session
    f += fx_worlds

    # create 'The Lord of the Rings'
    f.lord_of_rings = Franchise(name='The Lord of the Rings')
    f.lord_of_rings.world = f.middle_earth
    fx_session.add(f.lord_of_rings)

    # create 'Iron Man'
    f.iron_man = Franchise(name='Iron Man')
    f.iron_man.world = f.marvel_universe
    fx_session.add(f.iron_man)

    # create 'Captain America'
    f.captain_america = Franchise(name='Captain America')
    f.captain_america.world = f.marvel_universe
    fx_session.add(f.captain_america)

    # create 'Hulk'
    f.hulk = Franchise(name='Hulk')
    f.hulk.world = f.marvel_universe
    fx_session.add(f.hulk)

    # create 'Thor'
    f.thor = Franchise(name='Thor')
    f.thor.world = f.marvel_universe
    fx_session.add(f.thor)

    fx_session.flush()
    return f


@fixture
def fx_works(fx_session, fx_teams, fx_genres, fx_franchises):
    """Create *Cardcaptor Sakura* (comic book),
    which made by CLAMP members,
    which belongs to comic and romance genres.

    Create *The Lord of the Rings: The Fellowship of the Ring* (flim),
    which directed by Peter Jackson,
    which belongs to *The Lord of the Rings* franchise.

    Create *The Avengers* (flim),
    which belongs to *Iron Man*, *Captain America*, *Hulk*,
    and *Thor* franchise.
    """
    f = FixtureModule('fx_works')
    f += fx_teams
    f += fx_genres
    f += fx_franchises

    # create 'Cardcaptor Sakura'
    f.cardcaptor_sakura = Work(published_at=datetime.date(1996, 11, 22))
    f.cardcaptor_sakura.genres.update({f.comic, f.romance})
    fx_session.add(f.cardcaptor_sakura)

    sakura_title = Title(title='Cardcaptor Sakura')
    sakura_title.work = f.cardcaptor_sakura
    f.cardcaptor_sakura.titles.update({sakura_title})

    f.skura_member_asso_1 = Credit(role=Role.artist)
    f.skura_member_asso_1.work = f.cardcaptor_sakura
    f.skura_member_asso_1.person = f.clamp_member_1
    f.skura_member_asso_1.team = f.clamp
    fx_session.add(f.skura_member_asso_1)

    f.skura_member_asso_2 = Credit(role=Role.artist)
    f.skura_member_asso_2.work = f.cardcaptor_sakura
    f.skura_member_asso_2.person = f.clamp_member_2
    f.skura_member_asso_2.team = f.clamp
    fx_session.add(f.skura_member_asso_2)

    f.skura_member_asso_3 = Credit(role=Role.artist)
    f.skura_member_asso_3.work = f.cardcaptor_sakura
    f.skura_member_asso_3.person = f.clamp_member_3
    f.skura_member_asso_3.team = f.clamp
    fx_session.add(f.skura_member_asso_3)

    f.skura_member_asso_4 = Credit(role=Role.artist)
    f.skura_member_asso_4.work = f.cardcaptor_sakura
    f.skura_member_asso_4.person = f.clamp_member_4
    f.skura_member_asso_4.team = f.clamp
    fx_session.add(f.skura_member_asso_4)

    # create 'The Lord of the Rings: The Fellowship of the Ring'
    f.lord_of_rings_film = Work()
    fx_session.add(f.lord_of_rings_film)
    fx_session.flush()
    lor_title = Title(
        title='The Lord of the Rings: The Fellowship of the Ring'
    )
    lor_title.work = f.lord_of_rings_film
    f.lord_of_rings_film.titles.update({lor_title})
    f.lor_film_asso_1 = Credit(role=Role.director)
    f.lor_film_asso_1.work = f.lord_of_rings_film
    f.lor_film_asso_1.person = f.peter_jackson
    fx_session.add(f.lor_film_asso_1)
    f.lord_of_rings_film.franchises.update({f.lord_of_rings})

    # create 'The Avengers'
    f.avengers = Work()
    fx_session.add(f.avengers)
    fx_session.flush()
    avengers_title = Title(title='The Avengers')
    avengers_title.work = f.avengers
    f.avengers.titles.update({avengers_title})
    f.avengers.franchises.update({
        f.iron_man, f.captain_america, f.hulk, f.thor
    })

    fx_session.flush()
    return f


@fixture
def fx_cli_runner():
    return CliRunner()


@fixture
def fx_cfg_yml_file(fx_tmpdir):
    cfg_file = fx_tmpdir / 'test.cfg.yml'
    cfg = {
        'DATABASE_URL': 'sqlite:///:memory:'
    }
    with cfg_file.open('w') as f:
        dump(cfg, stream=f)
    return cfg_file


@fixture
def fx_flask_client():
    app.config['TESTING'] = True
    return app.test_client()


@fixture
def fx_celery_app():
    celery_app.conf['CELERY_ALWAYS_EAGER'] = True
    return celery_app
