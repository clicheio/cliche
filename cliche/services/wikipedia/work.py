""":mod:`cliche.services.wikipedia.work` --- Data entities for Wikipedia_
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All classes in this file are rdfs:domain of its columns.

.. _Wikipedia: http://wikipedia.org/

"""
from urllib.parse import unquote_plus

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ...orm import Base
from ...work import Work as ClicheWork


__all__ = ('ClicheWikipediaEdge', 'Entity', 'Relation', 'Artist', 'Work',
           'Film', 'Book')


def url_to_label(url):
    if url:
        return unquote_plus(url[28:].replace('_', ' ')).strip().lower()
    else:
        return None


class Entity(Base):
    """Representation of entities."""
    TYPE_PREDICATES = {}
    PROPERTIES = {
        'dbpedia-owl:wikiPageRevisionID',
        'rdfs:label',
        'dbpprop:country'
    }

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
                   label=item.get('label',
                                  url_to_label(item.get('name', None))),
                   country=url_to_label(item.get('country', None)))

    def get_identities(ontology='Thing'):
        return 'dbpedia-owl:' + ontology


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
    TYPE_PREDICATES = {
        'dbpedia-owl:writer',
        'dbpedia-owl:author',
        'dbpprop:author'
    }
    PROPERTIES = Entity.PROPERTIES | {'dbpedia-owl:notableWork'}

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


class Work(Entity):
    """Representation of work as an ontology."""
    PROPERTIES = Entity.PROPERTIES | {
        'dbpedia-owl:writer',
        'dbpedia-owl:author',
        'dbpedia-owl:mainCharacter',
        'dbpedia-owl:previousWork'
    }
    writer = Column(String)
    author = Column(String)
    main_character = Column(String)
    previous_work = Column(String)
    corres = relationship('ClicheWikipediaEdge', collection_class=set)

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


class Film(Work):
    """Representation of film as an ontology."""
    PROPERTIES = Work.PROPERTIES | {'dbpedia-owl:director'}

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


class Book(Work):
    """Representation of book as an ontology."""
    PROPERTIES = Work.PROPERTIES | {
        'dbpedia-owl:illustrator',
        'dbpedia-owl:isbn',
        'dbpedia-owl:numberOfPages'
    }

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


class ClicheWikipediaEdge(Base):
    """Correspondence between Works of Cliche and Wikipedia"""

    cliche_id = Column(Integer, ForeignKey('works.id'), primary_key=True)
    cliche_work = relationship(ClicheWork)
    wikipedia_name = Column(String, ForeignKey(Entity.name), primary_key=True)
    wikipedia_work = relationship(Entity)
    confidence = Column(Integer, default=0.5)

    __tablename__ = 'cliche_wikipedia_edge'
    __repr_columns__ = cliche_id, wikipedia_name, confidence
