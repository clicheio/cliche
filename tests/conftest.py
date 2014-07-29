import datetime
import os
import types

from pytest import fixture, yield_fixture

from cliche.people import Person, Team
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
def fx_people(fx_session):
    f = FixtureModule('fx_people')
    f.session = fx_session
    f.artist = Person(name='Nanase Ohkawa', dob=datetime.date(1967, 5, 2))
    fx_session.add(f.artist)
    f.artist_2 = Person(name='Mokona', dob=datetime.date(1968, 6, 16))
    fx_session.add(f.artist_2)
    f.artist_3 = Person(name='Tsubaki Nekoi', dob=datetime.date(1969, 1, 21))
    fx_session.add(f.artist_3)
    f.artist_4 = Person(name='Satsuki Igarashi', dob=datetime.date(1969, 2, 8))
    fx_session.add(f.artist_4)
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
