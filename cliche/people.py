""":mod:`cliche.people` --- Artists, teams, and editors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from sqlalchemy.schema import Column
from sqlalchemy.types import Date, DateTime, Integer, String

from .orm import Base

__all__ = {'Person', 'Team'}


class Person(Base):
    """People i.e. artists, editors."""

    #: (:class:`int`) The primary key integer.
    id = Column(Integer, primary_key=True)

    #: (:class:`str`) His/her name.
    name = Column(String, nullable=False, index=True)

    #: (:class:`datetime.date`) The date of birth.
    dob = Column(Date)

    #: (:class:`datetime.datetime`) The created time.
    created_at = Column(DateTime(timezone=True), nullable=False, index=True)

    __tablename__ = 'people'
    __repr_columns__ = id, name


class Team(Base):
    """Teams (including ad-hoc teams)."""

    #: (:class:`int`) The primary key integer.
    id = Column(Integer, primary_key=True)

    #: (:class:`str`) The team name (if it's named).
    name = Column(String, index=True)

    #: (:class:`datetime.datetime`) The created time.
    created_at = Column(DateTime(timezone=True), nullable=False, index=True)

    __tablename__ = 'teams'
    __repr_columns__ = id, name
