from sqlalchemy import Column, DateTime, ForeignKeyConstraint, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import and_

from ...orm import Base


__all__ = 'Entity', 'Relation'


class Entity(Base):
    """Representation of a TVTropes page."""

    namespace = Column(String, primary_key=True)
    name = Column(String, primary_key=True)
    url = Column(String)
    last_crawled = Column(DateTime)
    type = Column(String)

    relations = relationship(
        'Relation',
        foreign_keys=[namespace, name],
        primaryjoin=lambda:
            and_(Entity.namespace == Relation.origin_namespace,
                 Entity.name == Relation.origin),
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
