import os
import contextlib

from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool, StaticPool

from cliche.celery import app as celery_app
from cliche.orm import Base, Session
from cliche.web.app import app as flask_app

__all__ = ('DEFAULT_DATABASE_URL', 'get_database_url', 'get_engine',
           'get_session')


DEFAULT_DATABASE_URL = 'sqlite://'


def get_database_url(url=None):
    return url or os.environ.get(
        'CLICHE_TEST_DATABASE_URL',
        DEFAULT_DATABASE_URL
    )


def get_engine(url=None, echo=False):
    url = get_database_url(url)
    flask_app.config['DATABASE_URL'] = url
    connect_args = {}
    options = {'connect_args': connect_args, 'poolclass': NullPool}
    if url == DEFAULT_DATABASE_URL:
        # We have to use SQLite :memory: database across multiple threads
        # for testing.
        # http://bit.ly/1dF3SL3#using-a-memory-database-in-multiple-threads
        connect_args['check_same_thread'] = False
        options['poolclass'] = StaticPool
    engine = create_engine(url, echo=echo, **options)
    flask_app.config['DATABASE_ENGINE'] = engine
    celery_app.conf['DATABASE_ENGINE'] = engine
    return engine


@contextlib.contextmanager
def get_session(database_url=None, echo_sql=False):
    engine = get_engine(database_url, echo=echo_sql)
    try:
        metadata = Base.metadata
        metadata.drop_all(bind=engine)
        metadata.create_all(bind=engine)
        session = Session(bind=engine)
        yield session
        session.rollback()
        metadata.drop_all(bind=engine)
    finally:
        engine.dispose()
