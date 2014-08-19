""":mod:`cliche.work` --- Things associated with a creative work.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

from sqlalchemy.orm import relationship
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.sql.functions import now
from sqlalchemy.types import Date, DateTime, Enum, Integer, String

from .orm import Base
from .people import Person, Team

__all__ = (
    'Award',
    'AwardWinner',
    'Credit',
    'Genre',
    'Work',
    'WorkAward',
    'WorkGenre'
)

roles = (
    "Artist",
    "Author",
    "Editor"
)


class Award(Base):
    """Award won by the person or for the creative work."""

    #: (:class:`int`) The primary key integer.
    id = Column(Integer, primary_key=True)

    #: (:class:`str`) The name of the award.
    name = Column(String, nullable=False, index=True)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`AwardWinner`\ s that the award has.
    award_winners = relationship('AwardWinner', collection_class=set)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`cliche.people.Person`\ s that won the award.
    persons = relationship(Person,
                           secondary='award_winners',
                           collection_class=set)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`WorkAward`\ s that the award has.
    work_awards = relationship('WorkAward', collection_class=set)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`Work`\ s that won the award.
    works = relationship('Work',
                         secondary='work_awards',
                         collection_class=set)

    #: (:class:`datetime.datetime`) The date and time on which
    #: the record was created.
    created_at = Column(DateTime(timezone=True),
                        nullable=False,
                        default=now(),
                        index=True)

    __tablename__ = 'awards'
    __repr_columns__ = id, name


class AwardWinner(Base):
    """Relationship between the person and the award."""

    #: (:class:`int`) :class:`cliche.people.Person.id` of :attr:`person`.
    person_id = Column(Integer, ForeignKey(Person.id), primary_key=True)

    #: (:class:`cliche.people.Person`) The person that won the :attr:`award`.
    person = relationship(Person)

    #: (:class:`int`) :class:`Award.id` of :attr:`award`.
    award_id = Column(Integer, ForeignKey(Award.id), primary_key=True)

    #: (:class:`Award`) The award that the :attr:`person` won.
    award = relationship(Award)

    #: (:class:`datetime.datetime`) The date and time on which
    #: the record was created.
    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=now())

    __tablename__ = 'award_winners'
    __repr_columns__ = person_id, award_id


class Credit(Base):
    """Relationship between the work and the person.
    Describe that the person participated in making the work.
    """

    #: (:class:`int`) :class:`Work.id` of :attr:`work`.
    work_id = Column(Integer, ForeignKey('works.id'), primary_key=True)

    #: (:class:`Work`) The work which the :attr:`person` made.
    work = relationship('Work')

    #: (:class:`int`) :class:`cliche.people.Person.id` of :attr:`person`.
    person_id = Column(Integer, ForeignKey('people.id'), primary_key=True)

    #: (:class:`cliche.people.Person`) The person who made the :attr:`work`.
    person = relationship('Person')

    #: The person's role in making the work.
    role = Column(Enum(*roles, name='role'))

    #: (:class:`datetime.datetime`) The date and time on which
    #: the record was created.
    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=now())

    __tablename__ = 'credits'
    __repr_columns__ = person_id, work_id


class Genre(Base):
    """Genre of the creative work"""

    #: (:class:`int`) The primary key integer.
    id = Column(Integer, primary_key=True)

    #: (:class:`str`) The name of the genre.
    name = Column(String, nullable=False, index=True)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`WorkGenre`\ s that the genre has.
    work_genres = relationship('WorkGenre', collection_class=set)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`Work`\ s that fall into the genre.
    works = relationship('Work',
                         secondary='work_genres',
                         collection_class=set)

    #: (:class:`datetime.datetime`) The date and time on which
    #: the record was created.
    created_at = Column(DateTime(timezone=True),
                        nullable=False,
                        default=now(),
                        index=True)

    __tablename__ = 'genres'
    __repr_columns__ = id, name


class Work(Base):
    """Creative work i.e. book."""

    #: (:class:`int`) The primary key integer.
    id = Column(Integer, primary_key=True)

    #: (:class:`str`) The name of the work.
    name = Column(String, nullable=False, index=True)

    #: (:class:`datetime.date`) The publication date.
    published_at = Column(Date)

    #: (:class:`int`) The number of pages in the book.
    number_of_pages = Column(Integer)

    #: (:class:`str`) The ISBN of the book.
    isbn = Column(String)

    #: (:class:`int`) The :class:`cliche.people.Team.id` of :attr:`team`.
    team_id = Column(Integer, ForeignKey(Team.id))

    #: (:class:`cliche.people.Team`) The team that created the work.
    team = relationship(Team)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`WorkAward`\ s that the work has.
    work_awards = relationship('WorkAward', collection_class=set)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`Award`\ s that the work won.
    awards = relationship(Award,
                          secondary='work_awards',
                          collection_class=set)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`WorkGenre`\ s that the work has.
    work_genres = relationship('WorkGenre', collection_class=set)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`Genre`\ s that the work falls into.
    genres = relationship(Genre,
                          secondary='work_genres',
                          collection_class=set)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`Credit`\ s that the work has.
    credits = relationship(Credit, collection_class=set)

    #: (:class:`datetime.datetime`) The date and time on which
    #: the record was created.
    created_at = Column(DateTime(timezone=True),
                        nullable=False,
                        default=now(),
                        index=True)

    __tablename__ = 'works'
    __repr_columns__ = id, name


class WorkAward(Base):
    """Relationship between the work and the award."""

    #: (:class:`int`) :class:`Work.id` of :attr:`work`.
    work_id = Column(Integer, ForeignKey(Work.id), primary_key=True)

    #: (:class:`Work`) The work that won the :attr:`award`.
    work = relationship(Work)

    #: (:class:`int`) :class:`Award.id` of :attr:`award`.
    award_id = Column(Integer, ForeignKey(Award.id), primary_key=True)

    #: (:class:`Award`) The award that the :attr:`work` won.
    award = relationship(Award)

    #: (:class:`datetime.datetime`) The date and time on which
    #: the record was created.
    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=now())

    __tablename__ = 'work_awards'
    __repr_columns__ = work_id, award_id


class WorkGenre(Base):
    """Relationship between the work and the genre."""

    #: (:class:`int`) :class:`Work.id` of :attr:`work`.
    work_id = Column(Integer, ForeignKey(Work.id), primary_key=True)

    #: (:class:`Work`) The work that falls into the :attr:`genre`.
    work = relationship(Work)

    #: (:class:`int`) :class:`Genre.id` of :attr:`genre`.
    genre_id = Column(Integer, ForeignKey(Genre.id), primary_key=True)

    #: (:class:`Genre`) The genre into which the :attr:`work` falls.
    genre = relationship(Genre)

    #: (:class:`datetime.datetime`) The date and time on which
    #: the record was created.
    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=now())

    __tablename__ = 'work_genres'
    __repr_columns__ = work_id, genre_id
