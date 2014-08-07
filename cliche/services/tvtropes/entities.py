from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()


__all__ = 'Entity'


class Entity(Base):
    namespace = Column(String, primary_key=True)
    name = Column(String, primary_key=True)
    url = Column(String)
    last_crawled = Column(DateTime)
    type = Column(String)

    relations = relationship('Relation', foreign_keys=[namespace, name],
                             primaryjoin='and_(Entity.namespace == \
                                          Relation.origin_namespace, \
                                          Entity.name == Relation.origin)',
                             collection_class=set)

    def __init__(self, namespace, name, url, last_crawled, type):
        self.namespace = namespace
        self.name = name
        self.url = url
        self.last_crawled = last_crawled
        self.type = type

    def __repr__(self):
        return "<Entity('%s', '%s', '%s', '%s', '%s')" % (
            self.namespace, self.name, self.url, str(self.last_crawled),
            self.type
        )

    __tablename__ = 'entities'
    __repr_columns__ = namespace, name


class Relation(Base):
    origin_namespace = Column(String, ForeignKey(Entity.namespace),
                              primary_key=True)
    origin = Column(String, ForeignKey(Entity.name), primary_key=True)
    destination_namespace = Column(String, primary_key=True)
    destination = Column(String, primary_key=True)

    origin_entity = relationship('Entity',
                                 foreign_keys=[origin_namespace, origin])

    def __init__(self, origin_namespace, origin, destination_namespace,
                 destination):
        self.origin_namespace = origin_namespace
        self.origin = origin
        self.destination_namespace = destination_namespace
        self.destination = destination

    __tablename__ = 'relations'
    __repr_columns__ = origin_namespace, origin, destination_namespace, \
        destination
