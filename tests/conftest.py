import datetime
import os
import sqlite3
import types

from pytest import fixture, yield_fixture

from cliche.people import Person, Team
from cliche.work import Award, Genre, Work
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
def fx_awards(fx_session):
    f = FixtureModule('fx_awards')
    f.session = fx_session
    f.award = Award(name='Seiun Award')
    fx_session.add(f.award)
    f.award_2 = Award(name='Some Other Award')
    fx_session.add(f.award_2)
    fx_session.flush()
    return f


@fixture
def fx_people(fx_session, fx_awards):
    f = FixtureModule('fx_people')
    f += fx_awards
    f.artist = Person(name='Nanase Ohkawa', dob=datetime.date(1967, 5, 2))
    fx_session.add(f.artist)
    f.artist_2 = Person(name='Mokona', dob=datetime.date(1968, 6, 16))
    fx_session.add(f.artist_2)
    f.artist_3 = Person(name='Tsubaki Nekoi', dob=datetime.date(1969, 1, 21))
    fx_session.add(f.artist_3)
    f.artist_4 = Person(name='Satsuki Igarashi', dob=datetime.date(1969, 2, 8))
    fx_session.add(f.artist_4)
    f.person = Person(name='Some Person', dob=datetime.date(1990, 1, 1))
    f.person.awards.update({fx_awards.award_2})
    fx_session.add(f.person)
    fx_session.flush()
    return f


@fixture
def fx_teams(fx_session, fx_people):
    f = FixtureModule('fx_teams')
    f += fx_people
    f.team = Team(name='CLAMP')
    f.team.members.update({fx_people.artist, fx_people.artist_2,
                           fx_people.artist_3, fx_people.artist_4})
    fx_session.add(f.team)
    fx_session.flush()
    return f


@fixture
def fx_genres(fx_session):
    f = FixtureModule('fx_genres')
    f.session = fx_session
    f.genre = Genre(name='Comic')
    fx_session.add(f.genre)
    f.genre_2 = Genre(name='Romance')
    fx_session.add(f.genre_2)
    fx_session.flush()
    return f


@fixture
def fx_works(fx_session, fx_teams, fx_awards, fx_genres):
    f = FixtureModule('fx_works')
    f += fx_teams
    f += fx_awards
    f += fx_genres
    f.work = Work(name='Cardcaptor Sakura, Volume 1',
                  published_at=datetime.date(1996, 11, 22),
                  number_of_pages=187,
                  isbn='4063197433')
    f.work.team = f.team
    f.work.awards.update({f.award, f.award_2})
    f.work.genres.update({f.genre, f.genre_2})
    fx_session.add(f.work)
    fx_session.flush()
    return f
