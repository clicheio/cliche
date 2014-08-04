""":mod:`cliche.web.db` --- Database connections
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use :data:`session` in view functions.

"""
from flask import _app_ctx_stack, current_app, g
from sqlalchemy import create_engine
from werkzeug.local import LocalProxy

from ..orm import Session

__all__ = ('close_session', 'get_database_engine',
           'get_database_engine_options', 'get_session', 'session',
           'setup_session')


def get_database_engine():
    """Get a database engine.

    :returns: a database engine
    :rtype: :class:`sqlalchemy.engine.base.Engine`

    """
    config = current_app.config
    try:
        return config['DATABASE_ENGINE']
    except KeyError:
        db_url = config['DATABASE_URL']
        engine = create_engine(db_url, **get_database_engine_options())
        config['DATABASE_ENGINE'] = engine
        return engine


def get_database_engine_options():
    """Get a dictionary of options for SQLAlchemy engine.  These options
    are used by :func:`get_database_engine()` and passed to
    :func:`sqlalchemy.create_engine()` function.

    """
    return {}


def get_session():
    """Get a session.  If there's no yet, create one.

    :returns: a session
    :rtype: :class:`~cliche.orm.Session`

    """
    try:
        app_ctx_session = _app_ctx_stack.top.session
    except (AttributeError, RuntimeError):
        pass
    else:
        return app_ctx_session
    if hasattr(g, 'session'):
        return g.session
    sess = Session(bind=get_database_engine())
    try:
        g.session = sess
    except RuntimeError:
        pass
    return sess


def close_session(exception=None):
    """Close an established session."""
    if hasattr(g, 'session'):
        g.session.close()


def setup_session(app):
    """Setup the ``app`` to be able to use :data:`session`.

    :param app: the Flask application to setup
    :type app: :class:`~flask.Flask`

    """
    app.teardown_appcontext(close_session)


#: (:class:`~werkzeug.local.LocalProxy` of :class:`~cliche.orm.Session`)
#: The context local session.  Use this.
session = LocalProxy(get_session)
