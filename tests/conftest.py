import datetime
import os
import pathlib
import types

from click.testing import CliRunner
from pytest import fixture, yield_fixture
from yaml import dump

from cliche.people import Person, Team
from cliche.work import Award, Credit, Genre, Role, Work
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
def fx_awards(fx_session):
    # create awards: Seiun Awqrd, Hugo Awqrd and Nebula Award.
    f = FixtureModule('fx_awards')
    f.session = fx_session
    f.seiun_award = Award(name='Seiun Award')
    fx_session.add(f.seiun_award)
    f.hugo_award = Award(name='Hugo Award')
    fx_session.add(f.hugo_award)
    f.nebula_award = Award(name='Nebula Award')
    fx_session.add(f.nebula_award)
    fx_session.flush()
    return f


@fixture
def fx_people(fx_session, fx_awards):
    # create people: four artisits and Peter Jackson who won
    # Hugo and Nebula Award.
    f = FixtureModule('fx_people')
    f += fx_awards
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
    f.peter_jackson = Person(name='Peter Jackson',
                             dob=datetime.date(1961, 10, 31))
    f.peter_jackson.awards.update({fx_awards.hugo_award,
                                   fx_awards.nebula_award})
    fx_session.add(f.peter_jackson)
    fx_session.flush()
    return f


@fixture
def fx_teams(fx_session, fx_people):
    # create teams: CLAMP which consists of the four artists.
    f = FixtureModule('fx_teams')
    f += fx_people
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
    # create genres: Comic, Romance
    f = FixtureModule('fx_genres')
    f.session = fx_session
    f.comic = Genre(name='Comic')
    fx_session.add(f.comic)
    f.romance = Genre(name='Romance')
    fx_session.add(f.romance)
    fx_session.flush()
    return f


@fixture
def fx_works(fx_session, fx_teams, fx_awards, fx_genres):
    # create works: Cardcaptor Sakura which
    # made by CLAMP team and members of the team
    # , won Seiun Award
    # and belongs to comic and romance genres
    f = FixtureModule('fx_works')
    f += fx_teams
    f += fx_awards
    f += fx_genres
    f.cardcaptor_sakura = Work(name='Cardcaptor Sakura, Volume 1',
                               published_at=datetime.date(1996, 11, 22),
                               number_of_pages=187,
                               isbn='4063197433')
    f.cardcaptor_sakura.awards.update({f.seiun_award})
    f.cardcaptor_sakura.genres.update({f.comic, f.romance})
    fx_session.add(f.cardcaptor_sakura)
    fx_session.flush()
    f.skura_member_asso_1 = Credit(
        work_id=f.cardcaptor_sakura.id,
        person_id=f.clamp_member_1.id,
        role=Role.artist,
        team_id=f.clamp.id
    )
    fx_session.add(f.skura_member_asso_1)
    f.skura_member_asso_2 = Credit(
        work_id=f.cardcaptor_sakura.id,
        person_id=f.clamp_member_2.id,
        role=Role.artist,
        team_id=f.clamp.id
    )
    fx_session.add(f.skura_member_asso_2)
    f.skura_member_asso_3 = Credit(
        work_id=f.cardcaptor_sakura.id,
        person_id=f.clamp_member_3.id,
        role=Role.artist,
        team_id=f.clamp.id
    )
    fx_session.add(f.skura_member_asso_3)
    f.skura_member_asso_4 = Credit(
        work_id=f.cardcaptor_sakura.id,
        person_id=f.clamp_member_4.id,
        role=Role.artist,
        team_id=f.clamp.id
    )
    fx_session.add(f.skura_member_asso_4)
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
