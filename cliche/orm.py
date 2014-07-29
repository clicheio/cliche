""":mod:`cliche.orm` --- Object-relational mapping
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Cliche uses the relational database and data on the database
are mapped to objects.  It widely uses SQLAlchemy_ as its
ORM (object-relational mapping) framework.

In order to define a persist model class, just subclass :class:`Base`::

    from sqlalchemy import Column, Integer, UnicodeText

    from .orm import Base


    class Thing(Base):
        '''A something object-relationally mapped.'''

        id = Column(Integer, primary_key=True)
        value = Column(UnicodeText, nullable=False)
        __repr_columns = id, value
        __tablename__ = 'things'

.. _SQLAlchemy: http://www.sqlalchemy.org/

"""
import os.path
import pkgutil

from alembic.command import downgrade, stamp
from alembic.config import Config
from alembic.environment import EnvironmentContext
from alembic.script import ScriptDirectory
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

__all__ = {'Base', 'Session', 'downgrade_database', 'get_alembic_config',
           'get_database_revision', 'import_all_modules',
           'initialize_database', 'upgrade_database'}


#: SQLAlchemy declarative base class.
#:
#: .. attribute:: __repr_columns__
#:
#:    (:class:`collections.abc.Sequence`) This columns will be printed to
#:    :func:`repr()` string of its instances if :attr:`__repr_columns__`
#:    is defined.
#:
#: .. seealso::
#:
#:    SQLAlchemy --- :ref:`declarative_toplevel`
#:       Declarative allows all three to be expressed at once within the class
#:       declaration.
Base = declarative_base()

#: SQLAlchemy session class.
#:
#: .. seealso::
#:
#:    SQLAlchemy --- :ref:`session_toplevel`
#:       :mod:`~sqlalchemy.orm.session.Session` is the primary usage interface
#:       for persistence operations.
Session = sessionmaker(autocommit=True)


def make_repr(self):
    """Make a :func:`repr()` string for the given ``self`` object.
    If the class specified :attr:`~Base.__repr_columns__` it prints
    these attributes instead of its primary keys.

    :param self: an object to make a :func:`repr()` string
    :returns: a :func:`repr()` string
    :rtype: :class:`str`

    """
    cls = type(self)
    mod = cls.__module__
    name = ('' if mod == '__main__ ' else mod + '.') + cls.__qualname__
    try:
        columns = type(self).__repr_columns__
    except AttributeError:
        columns = cls.__mapper__.primary_key
    names = (column if isinstance(column, str) else column.name
             for column in columns)
    pairs = ((name, getattr(self, name))
             for name in names
             if hasattr(self, name))
    args = ' '.join(k + '=' + repr(v) for k, v in pairs)
    return '<{0} {1}>'.format(name, args)


Base.__repr__ = make_repr


def get_alembic_config(engine):
    """Creates a configuration for :mod:`alembic`.
    You can pass an :class:`~sqlalchemy.engine.base.Engine` object or
    a string of database url either.  So::

        from sqlalchemy import create_engine
        engine = create_engine('postgresql://localhost/cliche')
        alembic_cfg = get_alembic_config(engine)

    is equivalent to::

        db_url = 'postgresql://localhost/cliche'
        alembic_cfg = get_alembic_config(db_url)

    :param engine: the database engine to use
    :type engine: :class:`sqlalchemy.engine.base.Engine`, :class:`str`
    :returns: an alembic config
    :rtype: :class:`alembic.config.Config`

    """
    if isinstance(engine, Engine):
        url = str(engine.url)
    elif isinstance(engine, str):
        url = str(engine)
    else:
        raise TypeError('engine must be a string or an instance of sqlalchemy.'
                        'engine.base.Engine, not ' + repr(engine))
    cfg = Config()
    cfg.set_main_option('script_location', 'cliche:migrations')
    cfg.set_main_option('sqlalchemy.url', url)
    cfg.set_main_option('url', url)
    return cfg


def initialize_database(engine):
    """Creates all database schemas and stamps it as the head of versions.

    :param engine: the database engine to initialize
    :type engine: :class:`sqlalchemy.engine.base.Engine`

    """
    import_all_modules()
    Base.metadata.create_all(engine, checkfirst=False)
    alembic_cfg = get_alembic_config(engine)
    stamp(alembic_cfg, 'head')


def get_database_revision(engine):
    """Gets the current revision of the database.

    :param engine: the database engine to get the current revision
    :type engine: :class:`sqlalchemy.engine.base.Engine`
    :returns: the script of the current revision
    :rtype: :class:`alembic.script.Script`

    """
    config = get_alembic_config(engine)
    script = ScriptDirectory.from_config(config)
    result = [None]

    def get_revision(rev, context):
        result[0] = rev and script.get_revision(rev)
        return []
    with EnvironmentContext(config, script, fn=get_revision, as_sql=False,
                            destination_rev=None, tag=None):
        script.run_env()
    return result[0]


def upgrade_database(engine, revision='head'):
    """Upgrades the database schema to the chosen ``revision`` (default is
    head).

    :param engine: the database engine to upgrade
    :type engine: :class:`sqlalchemy.engine.base.Engine`
    :param revision: the revision to upgrade to.  default is ``'head'``
    :type revision: :class:`str`

    """
    config = get_alembic_config(engine)
    script = ScriptDirectory.from_config(config)

    def upgrade(rev, context):
        if rev is None and revision == 'head':
            import_all_modules()
            Base.metadata.create_all(engine)
            dest = script.get_revision(revision)
            context._update_current_rev(None, dest and dest.revision)
            return []
        return script._upgrade_revs(revision, rev)
    with EnvironmentContext(config, script, fn=upgrade, as_sql=False,
                            destination_rev=revision, tag=None):
        script.run_env()


def downgrade_database(engine, revision):
    """Reverts to a previous ``revision``.

    :param engine: the database engine to revert
    :type engine: :class:`sqlalchemy.engine.base.Engine`
    :param revision: the previous revision to revert to
    :type revision: :class:`str`

    """
    config = get_alembic_config(engine)
    downgrade(config, revision)


def import_all_modules():
    """Import all submodules of :mod:`cliche` to ensure every ORM
    entity classes are ready to use.  It's useful for being ready to
    auto-generate a migration script.

    """
    current_dir = os.path.join(os.path.dirname(__file__), '..')
    for _, mod, __ in pkgutil.walk_packages(current_dir):
        if mod.startswith('cliche.'):
            __import__(mod)
