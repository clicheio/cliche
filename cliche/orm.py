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
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

__all__ = 'Base', 'Session'


#: SQLAlchemy declarative base class.
#:
#: .. attribute:: __repr_columns__
#:
#:    (:class:`collections.Sequence`) This columns will be printed to
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
    name = ('' if mod == '__main__ ' else mod + '.') + cls.__name__
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
