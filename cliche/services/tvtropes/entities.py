from sqlalchemy import Column, DateTime, ForeignKeyConstraint, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import and_

from ...orm import Base


__all__ = 'Entity', 'Relation', 'Redirection'


class Entity(Base):
    """Representation of a TVTropes page."""

    namespace = Column(String, primary_key=True)
    name = Column(String, primary_key=True)
    url = Column(String, nullable=False)
    last_crawled = Column(DateTime(timezone=True))
    type = Column(String, nullable=False)

    relations = relationship(
        'Relation',
        foreign_keys=[namespace, name],
        primaryjoin=lambda:
            and_(Entity.namespace == Relation.origin_namespace,
                 Entity.name == Relation.origin),
        collection_class=set)

    aliases = relationship(
        'Redirection',
        foreign_keys=[namespace, name],
        primaryjoin=lambda:
            and_(Entity.namespace == Redirection.original_namespace,
                 Entity.name == Redirection.original),
        collection_class=set)

    __tablename__ = 'tvtropes_entities'
    __repr_columns__ = namespace, name


class Relation(Base):
    """Associate :class:`Entity` to other :class:`Entity`."""

    origin_namespace = Column(String, primary_key=True)
    origin = Column(String, primary_key=True)
    destination_namespace = Column(String, primary_key=True)
    destination = Column(String, primary_key=True)

    origin_entity = relationship('Entity',
                                 foreign_keys=[origin_namespace, origin])

    __table_args__ = (
        ForeignKeyConstraint(
            [origin_namespace, origin],
            [Entity.namespace, Entity.name]
        ),
    )

    __tablename__ = 'tvtropes_relations'
    __repr_columns__ = (origin_namespace, origin, destination_namespace,
                        destination)

class Redirection(Base):
    """Representation of an alias of :class:`Entity`."""

    alias_namespace = Column(String, primary_key=True)
    alias = Column(String, primary_key=True)
    original_namespace = Column(String, primary_key=True)
    original = Column(String, primary_key=True)

    original_entity = relationship('Entity',
                                   foreign_keys=[original_namespace,
                                                 original])

    __table_args__ = (
        ForeignKeyConstraint(
            [original_namespace, original],
            [Entity.namespace, Entity.name]
        ),
    )

    __tablename__ = 'tvtropes_redirections'
    __repr_columns__ = (alias_namespace, alias, original_namespace,
                        original)
