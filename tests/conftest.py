import datetime
import os
import pathlib
import types

from click.testing import CliRunner
from pytest import fixture, yield_fixture
from yaml import dump

from cliche.celery import app as celery_app
from cliche.name import Name
from cliche.people import Person, Team
from cliche.sqltypes import HashableLocale as Locale
from cliche.web.app import app
from cliche.work import Character, Credit, Franchise, Genre, Role, Work, World

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
    f.clamp_member_1 = Person(dob=datetime.date(1967, 5, 2))
    f.clamp_member_1.names.update({
        Name(nameable=f.clamp_member_1,
             name='Nanase Ohkawa',
             locale=Locale.parse('en_US'))
    })
    fx_session.add(f.clamp_member_1)
    f.clamp_member_2 = Person(dob=datetime.date(1968, 6, 16))
    f.clamp_member_2.names.update({
        Name(nameable=f.clamp_member_2,
             name='Mokona',
             locale=Locale.parse('en_US'))
    })
    fx_session.add(f.clamp_member_2)
    f.clamp_member_3 = Person(dob=datetime.date(1969, 1, 21))
    f.clamp_member_3.names.update({
        Name(nameable=f.clamp_member_3,
             name='Tsubaki Nekoi',
             locale=Locale.parse('en_US'))
    })
    fx_session.add(f.clamp_member_3)
    f.clamp_member_4 = Person(dob=datetime.date(1969, 2, 8))
    f.clamp_member_4.names.update({
        Name(nameable=f.clamp_member_4,
             name='Satsuki Igarashi',
             locale=Locale.parse('en_US'))
    })
    fx_session.add(f.clamp_member_4)

    # create 'Peter Jackson'
    f.peter_jackson = Person(dob=datetime.date(1961, 10, 31))
    f.peter_jackson.names.update({
        Name(nameable=f.peter_jackson,
             name='Peter Jackson',
             locale=Locale.parse('en_US'))
    })
    fx_session.add(f.peter_jackson)

    fx_session.flush()
    return f


@fixture
def fx_teams(fx_session, fx_people):
    """create teams: CLAMP which consists of the four artists"""
    f = FixtureModule('fx_teams')
    f += fx_people

    # create 'CLAMP' team
    f.clamp = Team()
    f.clamp.names.update({
        Name(nameable=f.clamp,
             name='CLAMP',
             locale=Locale.parse('en_US'))
    })
    f.clamp.members.update({f.clamp_member_1,
                            f.clamp_member_2,
                            f.clamp_member_3,
                            f.clamp_member_4})
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
    f.middle_earth = World()
    f.middle_earth.names.update({
        Name(nameable=f.middle_earth,
             name='Middle-earth',
             locale=Locale.parse('en_US'))
    })
    fx_session.add(f.middle_earth)

    # create 'Marvel Cinematic Universe'
    f.marvel_universe = World()
    f.marvel_universe.names.update({
        Name(nameable=f.marvel_universe,
             name='Marvel Cinematic Universe',
             locale=Locale.parse('en_US'))
    })
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
    f.lord_of_rings = Franchise()
    f.lord_of_rings.names.update({
        Name(nameable=f.lord_of_rings,
             name='The Lord of the Rings',
             locale=Locale.parse('en_US'))
    })
    f.lord_of_rings.world = f.middle_earth
    fx_session.add(f.lord_of_rings)

    # create 'Iron Man'
    f.iron_man = Franchise()
    f.iron_man.names.update({
        Name(nameable=f.iron_man,
             name='Iron Man',
             locale=Locale.parse('en_US'))
    })
    f.iron_man.world = f.marvel_universe
    fx_session.add(f.iron_man)

    # create 'Captain America'
    f.captain_america = Franchise()
    f.captain_america.names.update({
        Name(nameable=f.captain_america,
             name='Captain America',
             locale=Locale.parse('en_US'))
    })
    f.captain_america.world = f.marvel_universe
    fx_session.add(f.captain_america)

    # create 'Hulk'
    f.hulk = Franchise()
    f.hulk.names.update({
        Name(nameable=f.hulk,
             name='Hulk',
             locale=Locale.parse('en_US'))
    })
    f.hulk.world = f.marvel_universe
    fx_session.add(f.hulk)

    # create 'Thor'
    f.thor = Franchise()
    f.thor.names.update({
        Name(nameable=f.thor,
             name='Thor',
             locale=Locale.parse('en_US'))
    })
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

    Create *Iron Man* (flim),
    which belongs to *Iron Man* franchise.

    Create *Journey to the West* (novel)
    which is a Chinese novel published in the 16th century.

    Create *Saiyuki* (comic book)
    which is a Japanese comic book series
    and loosely based on the *Journey to the West*.

    Create *Saiyuki* (comic book)
    which is a Japanese comic book series
    and loosely based on the *Journey to the West*.

    Create *날아라 슈퍼보드* (anime)
    which is a korean animation series
    and loosely based on the *Journey to the West*.
    """
    f = FixtureModule('fx_works')
    f += fx_teams
    f += fx_genres
    f += fx_franchises

    # create 'Cardcaptor Sakura' combic book series
    f.cardcaptor_sakura = Work(published_at=datetime.date(1996, 11, 22))
    f.cardcaptor_sakura.genres.update({f.comic, f.romance})
    f.cardcaptor_sakura.names.update({
        Name(nameable=f.cardcaptor_sakura,
             name='Cardcaptor Sakura',
             locale=Locale.parse('en_US'))
    })
    fx_session.add(f.cardcaptor_sakura)

    f.skura_member_asso_1 = Credit(work=f.cardcaptor_sakura,
                                   person=f.clamp_member_1,
                                   team=f.clamp,
                                   role=Role.artist)
    fx_session.add(f.skura_member_asso_1)

    f.skura_member_asso_2 = Credit(work=f.cardcaptor_sakura,
                                   person=f.clamp_member_2,
                                   team=f.clamp,
                                   role=Role.artist)
    fx_session.add(f.skura_member_asso_2)

    f.skura_member_asso_3 = Credit(work=f.cardcaptor_sakura,
                                   person=f.clamp_member_3,
                                   team=f.clamp,
                                   role=Role.artist)
    fx_session.add(f.skura_member_asso_3)

    f.skura_member_asso_4 = Credit(work=f.cardcaptor_sakura,
                                   person=f.clamp_member_4,
                                   team=f.clamp,
                                   role=Role.artist)
    fx_session.add(f.skura_member_asso_4)

    # create 'The Lord of the Rings: The Fellowship of the Ring' film
    f.lord_of_rings_film = Work()
    f.lord_of_rings_film.names.update({
        Name(nameable=f.lord_of_rings_film,
             name='The Lord of the Rings: The Fellowship of the Ring',
             locale=Locale.parse('en_US'))
    })
    f.lor_film_asso_1 = Credit(
        work=f.lord_of_rings_film,
        person=f.peter_jackson,
        role=Role.director
    )
    fx_session.add(f.lor_film_asso_1)
    f.lord_of_rings_film.franchises.update({f.lord_of_rings})
    fx_session.add(f.lord_of_rings_film)

    # create 'The Avengers' film
    f.avengers = Work()
    f.avengers.names.update({
        Name(nameable=f.avengers,
             name='The Avengers',
             locale=Locale.parse('en_US'))
    })
    f.avengers.franchises.update({
        f.iron_man, f.captain_america, f.hulk, f.thor
    })
    fx_session.add(f.avengers)

    # create 'Iron Man' film
    f.iron_man_film = Work()
    f.iron_man_film.names.update({
        Name(nameable=f.iron_man_film,
             name='Iron Man',
             locale=Locale.parse('en_US'))
    })
    f.iron_man_film.franchises.update({f.iron_man})
    fx_session.add(f.iron_man_film)

    # create 'Journey to the West' novel
    f.journey_west = Work()
    f.journey_west.names.update({
        Name(nameable=f.journey_west,
             name='Journey to the West',
             locale=Locale.parse('en_US')),
        Name(nameable=f.journey_west,
             name='서유기',
             locale=Locale.parse('ko_KR'))
    })
    fx_session.add(f.journey_west)

    # create 'Saiyuki' comic book series
    f.saiyuki = Work()
    f.saiyuki.names.update({
        Name(nameable=f.saiyuki,
             name='Saiyuki',
             locale=Locale.parse('en_US')),
        Name(nameable=f.saiyuki,
             name='환상마전 최유기',
             locale=Locale.parse('ko_KR'))
    })
    fx_session.add(f.saiyuki)

    # create '날아라 슈퍼보드' animation series
    f.superboard = Work()
    f.superboard.names.update({
        Name(nameable=f.superboard,
             name='날아라 슈퍼보드',
             locale=Locale.parse('ko_KR'))
    })
    fx_session.add(f.superboard)

    fx_session.flush()
    return f


@fixture
def fx_characters(fx_session, fx_works):
    """create fictional characters: Iron Man, Hulk, Frodo, Xuanzang,
    and some characters who is derived from Xuanzang
    """
    f = FixtureModule('fx_characters')
    f += fx_works

    # create 'Iron Man' character
    f.iron_man_character = Character()
    f.iron_man_character.names.update({
        Name(nameable=f.iron_man_character,
             name='Iron Man',
             locale=Locale.parse('en_US'))
    })
    fx_works.avengers.characters.update({f.iron_man_character})
    fx_works.iron_man_film.characters.update({f.iron_man_character})

    # create 'Hulk' character
    f.hulk_character = Character()
    f.hulk_character.names.update({
        Name(nameable=f.hulk_character,
             name='Hulk',
             locale=Locale.parse('en_US'))
    })
    fx_works.avengers.characters.update({f.hulk_character})

    # create 'Frodo Baggins' character
    f.frodo = Character()
    f.frodo.names.update({
        Name(nameable=f.frodo,
             name='Frodo Baggins',
             locale=Locale.parse('en_US'))
    })
    fx_works.lord_of_rings_film.characters.update({f.frodo})

    # create 'Xuanzang' character
    f.xuanzang = Character()
    f.xuanzang.names.update({
        Name(nameable=f.xuanzang,
             name='Xuanzang',
             locale=Locale.parse('en_US')),
        Name(nameable=f.xuanzang,
             name='삼장',
             locale=Locale.parse('ko_KR'))
    })
    fx_works.journey_west.characters.update({f.xuanzang})

    # create 'Genjo Sanzo' character
    f.sanzo = Character()
    f.sanzo.names.update({
        Name(nameable=f.sanzo,
             name='Genjo Sanzo',
             locale=Locale.parse('en_US')),
        Name(nameable=f.sanzo,
             name='삼장',
             locale=Locale.parse('ko_KR'))
    })
    f.sanzo.original_character = f.xuanzang
    fx_works.saiyuki.characters.update({f.sanzo})

    # create '삼장 법사' who is appeared in '날아라 슈퍼보드'
    f.samjang = Character()
    f.samjang.names.update({
        Name(nameable=f.samjang,
             name='삼장 법사',
             locale=Locale.parse('ko_KR'))
    })
    f.samjang.original_character = f.xuanzang
    fx_works.saiyuki.characters.update({f.samjang})

    with fx_session.begin():
        fx_session.add_all([f.iron_man_character, f.hulk_character, f.frodo,
                            f.xuanzang, f.sanzo, f.samjang])
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
