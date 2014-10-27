""":mod:`cliche.services.wikipedia.work` --- Data entities for Wikipedia_
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. _Wikipedia: http://wikipedia.org/

"""
from sqlalchemy import Column, Integer, String

from ...orm import Base


__all__ = 'Entity', 'Relation'


class Entity(Base):
    """Representation of entities."""
    name = Column(String, primary_key=True)
    revision = Column(Integer)
    label = Column(String)
    country = Column(String)

    __tablename__ = 'wikipedia_entities'
    __repr_columns__ = name, revision, label, country


class Relation(Base):
    """Representation of relations."""

    work = Column(String, primary_key=True)
    work_label = Column(String)
    author = Column(String)
    author_label = Column(String)
    revision = Column(Integer)

    __tablename__ = 'wikipedia_relations'
    __repr_columns__ = work, work_label, author, author_label, revision
