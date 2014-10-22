""":mod:`cliche.people` --- Artists, teams, and editors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.sql.functions import now
from sqlalchemy.types import Date, DateTime, Integer

from .name import Nameable
from .orm import Base
from .sqltypes import prevent_discriminator_from_changing

__all__ = 'Person', 'Team', 'TeamMembership'


class Person(Nameable):
    """People i.e. artists, editors."""

    #: (:class:`int`) The primary key integer.
    id = Column(Integer, ForeignKey(Nameable.id), primary_key=True)

    #: (:class:`datetime.date`) The date of birth.
    dob = Column(Date)

    #: (:class:`datetime.date`) The date of death.
    dod = Column(Date)

    #: (:class:`datetime.datetime`) The created time.
    created_at = Column(DateTime(timezone=True),
                        nullable=False,
                        default=now(),
                        index=True)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`TeamMembership`\ s he/she has.
    memberships = relationship('TeamMembership',
                               cascade='delete, merge, save-update',
                               collection_class=set)

    #: (:class:`collections.abc.MutableSet`) The set of :class:`Team`\ s
    #: he/she belongs to.
    teams = relationship('Team',
                         secondary='team_memberships',
                         collection_class=set)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`cliche.work.Credit`\ s that the person has.
    credits = relationship('Credit',
                           cascade='delete, merge, save-update',
                           collection_class=set)

    __tablename__ = 'people'
    __repr_columns__ = [id]
    __mapper_args__ = {
        'polymorphic_identity': 'people',
    }


class Team(Nameable):
    """Teams (including ad-hoc teams)."""

    #: (:class:`int`) The primary key integer.
    id = Column(Integer, ForeignKey(Nameable.id), primary_key=True)

    #: (:class:`datetime.datetime`) The created time.
    created_at = Column(DateTime(timezone=True),
                        nullable=False,
                        default=now(),
                        index=True)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`TeamMembership`\ s that the team has.
    memberships = relationship('TeamMembership',
                               cascade='delete, merge, save-update',
                               collection_class=set)

    #: (:class:`collections.abc.MutableSet`) The members :class:`Person` set.
    members = relationship(Person,
                           secondary='team_memberships',
                           collection_class=set)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`cliche.work.Credit`\ s in which the team was involved.
    credits = relationship('Credit', collection_class=set)

    __tablename__ = 'teams'
    __repr_columns__ = [id]
    __mapper_args__ = {
        'polymorphic_identity': 'teams',
    }


class TeamMembership(Base):
    """Team memberships to people."""

    #: (:class:`int`) :class:`Team.id` of :attr:`team`.
    team_id = Column(Integer, ForeignKey(Team.id), primary_key=True)

    #: (:class:`Team`) The team that the :attr:`member` belongs to.
    team = relationship(Team)

    #: (:class:`int`) :class:`Person.id` of :attr:`member`.
    member_id = Column(Integer, ForeignKey(Person.id), primary_key=True)

    #: (:class:`Person`) The member who is a member of the :attr:`team`.
    member = relationship(Person)

    #: (:class:`datetime.datetime`) The added time.
    created_at = Column(DateTime(timezone=True), nullable=False, default=now())

    __tablename__ = 'team_memberships'
    __repr_columns__ = team_id, member_id


prevent_discriminator_from_changing(Person.type)
prevent_discriminator_from_changing(Team.type)
