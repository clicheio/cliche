""":mod:`cliche.services.wikipedia.WorkAuthor` --- Data entities for Wikipedia_
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. _Wikipedia: http://wikipedia.org/

"""
from sqlalchemy import Column, String

from ...orm import Base


__all__ = 'WorkAuthor'


class WorkAuthor(Base):
    """Representation of a work."""

    work = Column(String, primary_key=True)
    author = Column(String)

    __tablename__ = 'wikipedia_works'
    __repr_columns__ = work, author
