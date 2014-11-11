""":mod:`cliche.user` --- Users
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.sql.functions import now
from sqlalchemy.types import DateTime, Integer, String

from .orm import Base


__all__ = 'User',


class User(Base):
    """Registered user in cliche.io with social providers."""

    #: (:class:`int`) The primary key integer.
    id = Column(Integer, primary_key=True)

    #: (:class:`str`) The name for using in user list.
    name = Column(String, nullable=False)

    #: (:class:`collections.abc.MutableSet`) The credentials matched.
    credentials = relationship('Credential', collection_class=set)

    #: (:class:`datetime.datetime`) The date and time on which
    #: the record was created.
    created_at = Column(DateTime(timezone=True), nullable=False, default=now())

    __tablename__ = 'users'
    __repr_columns__ = id, name


class Credential(Base):
    """Information about user account from social providers."""

    #: (:class:`int`) The primary key integer.
    id = Column(Integer, primary_key=True)

    #: (:class:`str`) The provider name
    provider = Column(String, nullable=False)

    #: (:class:`int`) user id from :class:`cliche.user.User`
    user_id = Column(Integer, ForeignKey('users.id'))

    #: (:class:`cliche.user.User`) user
    user = relationship(User)

    #: (:class:`datetime.datetime`) The date and time on which
    #: the record was created.
    created_at = Column(DateTime(timezone=True), nullable=False, default=now())

    __tablename__ = 'credential'
    __mapper_args__ = {'polymorphic_on': provider}
    __repr_columns__ = id, provider
