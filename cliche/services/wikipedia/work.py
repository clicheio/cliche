""":mod:`cliche.services.wikipedia.work` --- Data entities for Wikipedia_
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. _Wikipedia: http://wikipedia.org/

"""
from sqlalchemy import Column, Integer, String

from ...orm import Base


__all__ = 'Work',


class Work(Base):
    """Representation of a work."""

    work = Column(String, primary_key=True)
    revision = Column(Integer)
    author = Column(String)

    __tablename__ = 'wikipedia_works'
    __repr_columns__ = work, revision, author
