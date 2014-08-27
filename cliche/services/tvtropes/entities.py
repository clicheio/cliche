""":mod:`cliche.services.tvtropes.entities` --- Data entities for TVTropes_
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. _TVTropes: http://tvtropes.org/

"""
from sqlalchemy import Column, DateTime, ForeignKeyConstraint, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import and_

from ...orm import Base


__all__ = 'Entity', 'Redirection', 'Relation'


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
                 Entity.name == Relation.origin_name),
        collection_class=set)

    aliases = relationship(
        'Redirection',
        foreign_keys=[namespace, name],
        primaryjoin=lambda:
            and_(Entity.namespace == Redirection.original_namespace,
                 Entity.name == Redirection.original_name),
        collection_class=set)

    __tablename__ = 'tvtropes_entities'
    __repr_columns__ = namespace, name


class Redirection(Base):
    """Representation of an alias of :class:`Entity`."""

    alias_namespace = Column(String, primary_key=True)
    alias_name = Column(String, primary_key=True)
    original_namespace = Column(String, primary_key=True)
    original_name = Column(String, primary_key=True)

    original_entity = relationship('Entity',
                                   foreign_keys=[original_namespace,
                                                 original_name])

    __table_args__ = (
        ForeignKeyConstraint(
            [original_namespace, original_name],
            [Entity.namespace, Entity.name]
        ),
    )

    __tablename__ = 'tvtropes_redirections'
    __repr_columns__ = (alias_namespace, alias_name, original_namespace,
                        original_name)


class Relation(Base):
    """Associate :class:`Entity` to other :class:`Entity`."""

    origin_namespace = Column(String, primary_key=True)
    origin_name = Column(String, primary_key=True)
    destination_namespace = Column(String, primary_key=True)
    destination_name = Column(String, primary_key=True)

    origin_entity = relationship('Entity',
                                 foreign_keys=[origin_namespace, origin_name])

    __table_args__ = (
        ForeignKeyConstraint(
            [origin_namespace, origin_name],
            [Entity.namespace, Entity.name]
        ),
    )
    __tablename__ = 'tvtropes_relations'
    __repr_columns__ = (origin_namespace, origin_name, destination_namespace,
                        destination_name)
