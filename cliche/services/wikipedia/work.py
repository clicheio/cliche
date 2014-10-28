""":mod:`cliche.services.wikipedia.work` --- Data entities for Wikipedia_
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All classes in this file are rdfs:domain of its columns.

.. _Wikipedia: http://wikipedia.org/

"""
from sqlalchemy import Column, Integer, String

from ...orm import Base


__all__ = 'Entity', 'Relation', 'Artist', 'Work', 'Film'


class Entity(Base):
    """Representation of entities."""
    name = Column(String, primary_key=True)
    revision = Column(Integer)
    label = Column(String)
    country = Column(String)
    type = Column(String(20))

    __tablename__ = 'wikipedia_entities'
    __repr_columns__ = name, revision, label, country
    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'entity'
    }


class Relation(Base):
    """Representation of relations."""

    work = Column(String, primary_key=True)
    work_label = Column(String)
    author = Column(String)
    author_label = Column(String)
    revision = Column(Integer)

    __tablename__ = 'wikipedia_relations'
    __repr_columns__ = work, work_label, author, author_label, revision


class Artist(Entity):
    """Representation of artist as an ontology."""
    notableWork = Column(String)
    type = Column(String(20))

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'artist'
    }


class Work(Entity):
    """Representation of work as an ontology."""
    writer = Column(String)
    author = Column(String)
    mainCharacter = Column(String)
    previousWork = Column(String)
    type = Column(String(20))

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'work'
    }


class Film(Work):
    """Representation of film as an ontology."""
    director = Column(String)
    __mapper_args__ = {
        'polymorphic_identity': 'film'
    }
