""":mod:`cliche.work` --- Works
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.sql.functions import now
from sqlalchemy.types import Date, DateTime, Integer, String

from .orm import Base
from .people import Team

__all__ = 'Work',


class Work(Base):
    """Work i.e. Book."""

    #: (:class:`int`) The primary key integer.
    id = Column(Integer, primary_key=True)

    #: (:class:`str`) Title.
    title = Column(String, nullable=False, index=True)

    #: (:class:`datetime.date`) Published date.
    dop = Column(Date)

    #: (:class:`int`) Author team id.
    team_id = Column(Integer, ForeignKey(Team.id))

    #: (:class:`cliche.people.Team`) Author team.
    team = relationship(Team)

    #: (:class:`datetime.datetime`) The added time.
    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=now())

    __tablename__ = 'works'
    __repr_columns__ = id, title
