""":mod:`cliche.services.tvtropes.entities` --- Data entities for TVTropes_
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. _TVTropes: http://tvtropes.org/

"""
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Column, ForeignKey, ForeignKeyConstraint
from sqlalchemy.sql.expression import and_
from sqlalchemy.types import DateTime, Integer, String

from ...orm import Base
from ...work import Work


__all__ = 'ClicheTvtropesEdge', 'Entity', 'Redirection', 'Relation'


class Entity(Base):
    """Representation of a TVTropes page."""

    namespace = Column(String, primary_key=True)
    name = Column(String, primary_key=True)
    url = Column(String, nullable=False)
    last_crawled = Column(DateTime(timezone=True))
    type = Column(String, nullable=False)

    relations = relationship(
        lambda: Relation,
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

    corres = relationship('ClicheTvtropesEdge', collection_class=set)

    __tablename__ = 'tvtropes_entities'
    __repr_columns__ = namespace, name


class Redirection(Base):
    """Representation of an alias of :class:`Entity`."""

    alias_namespace = Column(String, primary_key=True)
    alias_name = Column(String, primary_key=True)
    original_namespace = Column(String, nullable=False)
    original_name = Column(String, nullable=False)

    original_entity = relationship(lambda: Entity,
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

    origin_entity = relationship(lambda: Entity,
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


class ClicheTvtropesEdge(Base):
    """Correspondence between Works of Cliche and TV Tropes"""

    cliche_id = Column(Integer, ForeignKey(Work.id), primary_key=True)
    cliche_work = relationship(Work)
    tvtropes_namespace = Column(String, primary_key=True)
    tvtropes_name = Column(String, primary_key=True)
    tvtropes_entity = relationship(Entity,
                                   foreign_keys=[tvtropes_namespace,
                                                 tvtropes_name])
    confidence = Column(Integer, default=0.5)

    __tablename__ = 'cliche_tvtropes_edges'
    __table_args__ = (
        ForeignKeyConstraint(
            [tvtropes_namespace, tvtropes_name],
            [Entity.namespace, Entity.name]
        ),
    )
    __repr_columns__ = (cliche_id, tvtropes_namespace, tvtropes_name,
                        confidence)
