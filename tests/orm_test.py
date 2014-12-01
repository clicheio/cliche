import functools
import os
import sys
import tempfile

from pytest import fixture
from sqlalchemy import create_engine

from cliche.orm import (downgrade_database, get_database_revision,
                        import_all_modules, initialize_database,
                        upgrade_database)


@fixture
def tmp_engine(request):
    """An empty SQLite database."""
    _, filename = tempfile.mkstemp()
    engine = create_engine('sqlite:///' + filename)
    request.addfinalizer(functools.partial(os.remove, filename))
    return engine


def test_initialize(tmp_engine):
    initialize_database(tmp_engine)
    script = get_database_revision(tmp_engine)
    assert script.is_head


def test_upgrade_downgrade(tmp_engine):
    rev = '27e81ea4d86'
    upgrade_database(tmp_engine, rev)
    script = get_database_revision(tmp_engine)
    assert not script.is_head
    assert script.revision == rev
    downgrade_database(tmp_engine, 'base')
    script = get_database_revision(tmp_engine)
    assert not script


def test_import_all_modules():
    modules = import_all_modules()
    for mod in modules:
        assert mod.startswith('cliche.')
    assert modules <= frozenset(sys.modules)
