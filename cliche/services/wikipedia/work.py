""":mod:`cliche.services.wikipedia.work` --- Data entities for Wikipedia_
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All classes in this file are rdfs:domain of its columns.

.. _Wikipedia: http://wikipedia.org/

"""
from sqlalchemy import Column, DateTime, Integer, String

from ...orm import Base


__all__ = 'Entity', 'Relation', 'Artist', 'Work', 'Film', 'Book'


class Entity(Base):
    """Representation of entities."""

    name = Column(String, primary_key=True)
    revision = Column(Integer)
    label = Column(String)
    country = Column(String)
    last_crawled = Column(DateTime(timezone=True), nullable=False)
    type = Column(String(20))

    __tablename__ = 'wikipedia_entities'
    __repr_columns__ = name, revision, label, country
    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'entity'
    }

    @classmethod
    def initialize(cls, item):
        return cls(name=item.get('name', None),
                   revision=item.get('wikiPageRevisionID', None),
                   label=item.get('label', None),
                   country=item.get('country', None))

    def get_identities(ontology='Thing'):
        return 'dbpedia-owl:' + ontology

    def get_entities():
        entities = [
            'dbpedia-owl:wikiPageRevisionID',
            'rdfs:label',
            'dbpprop:country',
        ]
        return entities

    def get_properties():
        return []


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

    notable_work = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'artist'
    }

    @classmethod
    def initialize(cls, item):
        temp = super().initialize(item)
        temp.notable_work = item.get('notableWork', None)
        return temp

    def get_identities():
        return 'dbpedia-owl:Artist'

    def get_entities():
        return Entity.get_entities() + ['dbpedia-owl:notableWork']

    def get_properties():
        p = [
            'dbpedia-owl:writer',
            'dbpedia-owl:author',
            'dbpedia-owl:author'
        ]
        return p


class Work(Entity):
    """Representation of work as an ontology."""

    writer = Column(String)
    author = Column(String)
    main_character = Column(String)
    previous_work = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'work'
    }

    @classmethod
    def initialize(cls, item):
        temp = super().initialize(item)
        temp.writer = item.get('writer', None)
        temp.author = item.get('author', None)
        temp.main_character = item.get('mainCharacter', None)
        temp.previous_work = item.get('previousWork', None)
        return temp

    def get_identities():
        return 'dbpedia-owl:Work'

    def get_entities():
        entities = [
            'dbpedia-owl:writer',
            'dbpedia-owl:author',
            'dbpedia-owl:mainCharacter',
            'dbpedia-owl:previousWork',
        ]
        return Entity.get_entities() + entities


class Film(Work):
    """Representation of film as an ontology."""

    director = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'film'
    }

    @classmethod
    def initialize(cls, item):
        temp = super().initialize(item)
        temp.director = item.get('director', None)
        return temp

    def get_identities():
        return 'dbpedia-owl:Film'

    def get_entities():
        return Work.get_entities() + ['dbpedia-owl:director']


class Book(Work):
    """Representation of book as an ontology."""

    illustrator = Column(String)
    isbn = Column(String)
    number_of_pages = Column(Integer)

    __mapper_args__ = {
        'polymorphic_identity': 'book'
    }

    @classmethod
    def initialize(cls, item):
        temp = super().initialize(item)
        temp.illustrator = item.get('illustrator', None)
        temp.isbn = item.get('isbn', None)
        temp.number_of_pages = item.get('numberOfPages', None)
        return temp

    def get_identities():
        return 'dbpedia-owl:Book'

    def get_entities():
        entities = [
            'dbpedia-owl:illustrator',
            'dbpedia-owl:isbn',
            'dbpedia-owl:numberOfPages',
        ]
        return Work.get_entities() + entities
