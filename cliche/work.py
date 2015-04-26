""":mod:`cliche.work` --- Things associated with a creative work.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import enum

from sqlalchemy.orm import foreign, relationship, remote
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.sql.functions import now
from sqlalchemy.types import Date, DateTime, Integer, String

from .name import Nameable
from .orm import Base
from .sqltypes import EnumType, prevent_discriminator_from_changing

__all__ = ('Character', 'Credit', 'Franchise', 'Genre', 'Role',
           'Work', 'WorkCharacter', 'WorkFranchise', 'WorkGenre', 'World')


class Role(enum.Enum):
    """Python enum type to describe role of him/her in making a work."""

    artist = 'artist'
    author = 'author'
    director = 'director'
    editor = 'editor'
    unknown = 'unknown'


class Character(Nameable):
    """Fictional character that appears in creative work."""

    #: (:class:`int`) The primary key integer.
    id = Column(Integer, ForeignKey(Nameable.id), primary_key=True)

    #: (:class:'int') :class:`Character.id` of :attr:`original_character`.
    original_character_id = Column(Integer, ForeignKey('characters.id'))

    #: (:class:'Character') The original character from which this character
    #: is derived.
    original_character = relationship(
        'Character',
        primaryjoin=foreign(original_character_id) == remote(id)
    )

    #: (:class:'collections.abc.MutableSet') The set of :class:`Character`\ s
    #: which is derived from this character
    derived_characters = relationship(
        'Character',
        primaryjoin=remote(original_character_id) == id,
        collection_class=set
    )

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`Work`\ s in which the character appeared.
    works = relationship('cliche.work.Work',
                         secondary='work_characters',
                         collection_class=set)

    __tablename__ = 'characters'
    __repr_columns__ = [id]
    __mapper_args__ = {
        'polymorphic_identity': 'characters',
    }


class Credit(Base):
    """Relationship between the work, the person, and the team.
    Describe that the person participated in making the work.
    """

    #: (:class:`int`) :class:`Work.id` of :attr:`work`.
    work_id = Column(Integer, ForeignKey('works.id'), primary_key=True)

    #: (:class:`Work`) The work which the :attr:`person` made.
    work = relationship(lambda: Work)

    #: (:class:`int`) :class:`cliche.people.Person.id` of :attr:`person`.
    person_id = Column(Integer, ForeignKey('people.id'), primary_key=True)

    #: (:class:`cliche.people.Person`) The person who made the :attr:`work`.
    person = relationship('Person')

    #: The person's role in making the work.
    role = Column(EnumType(Role, name='credits_role'),
                  primary_key=True, default=Role.unknown)

    #: (:class:`int`) :class:`Team.id` of :attr:`team`. (optional)
    team_id = Column(Integer, ForeignKey('teams.id'))

    #: The team which the person belonged when work had been made.
    team = relationship('Team')

    #: (:class:`datetime.datetime`) The date and time on which
    #: the record was created.
    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=now())

    __tablename__ = 'credits'
    __repr_columns__ = person_id, work_id, role, team_id


class Franchise(Nameable):
    """Multimedia franchise that is a franchise for which installments
    exist in multiple forms of media, such as books, comic books, and films,
    for example *The Lord of the Rings* and *Iron Man*.
    """

    #: (:class:`int`) The primary key integer.
    id = Column(Integer, ForeignKey(Nameable.id), primary_key=True)

    #: (:class:`int`) :class:`World.id` of :attr:`world`.
    world_id = Column(Integer, ForeignKey('worlds.id'))

    #: (:class:`World`) The world which the franchise belongs to.
    world = relationship('World', foreign_keys=[world_id])

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`WorkFranchise`\ s that the franchise has.
    work_franchises = relationship('WorkFranchise',
                                   cascade='delete, merge, save-update',
                                   collection_class=set)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`Work`\ s that belongs to the franchise.
    works = relationship(lambda: Work,
                         secondary='work_franchises',
                         collection_class=set)

    #: (:class:`datetime.datetime`) The date and time on which
    #: the record was created.
    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=now())

    __tablename__ = 'franchises'
    __repr_columns__ = [id]
    __mapper_args__ = {
        'polymorphic_identity': 'franchises',
    }


class Genre(Base):
    """Genre of the creative work"""

    #: (:class:`int`) The primary key integer.
    id = Column(Integer, primary_key=True)

    #: (:class:`str`) The name of the genre.
    name = Column(String, nullable=False, index=True)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`WorkGenre`\ s that the genre has.
    work_genres = relationship('WorkGenre',
                               cascade='delete, merge, save-update',
                               collection_class=set)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`Work`\ s that fall into the genre.
    works = relationship(lambda: Work,
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


class Trope(Base):  # FIXME: Temporary, It not extend Nameable.
    """Tropes"""

    #: (:class:`int`) The primary key integer.
    id = Column(Integer, primary_key=True)

    #: (:class:`str`) Trope name
    name = Column(String, nullable=False)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`WorkTrope`.
    work_tropes = relationship('WorkTrope',
                               cascade='delete, merge, save-update',
                               collection_class=set)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`Work`.
    works = relationship(lambda: Work, secondary='work_tropes',
                         collection_class=set)

    __tablename__ = 'tropes'
    __repr_columns__ = id, name


class Work(Nameable):
    """Creative work(s) that could be a single work like a film, or
    a series of works such as a combic book series and a television series.
    """

    #: (:class:`int`) The primary key integer.
    id = Column(Integer, ForeignKey(Nameable.id), primary_key=True)

    #: (:class:`str`) Work media type.
    media_type = Column(String, nullable=False)

    #: (:class:`datetime.date`) The publication date.
    published_at = Column(Date)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`WorkGenre`\ s that the work has.
    work_genres = relationship('WorkGenre',
                               cascade='delete, merge, save-update',
                               collection_class=set)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`Genre`\ s that the work falls into.
    genres = relationship(Genre,
                          secondary='work_genres',
                          collection_class=set)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`Credit`\ s that the work has.
    credits = relationship(Credit,
                           cascade='delete, merge, save-update',
                           collection_class=set)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`WorkFranchise`\ s that the work has.
    work_franchises = relationship('WorkFranchise',
                                   cascade='delete, merge, save-update',
                                   collection_class=set)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`Franchise`\ s that the work belongs to.
    franchises = relationship(Franchise,
                              secondary='work_franchises',
                              collection_class=set)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`Character`\ s that appeared in the work.
    characters = relationship(Character,
                              secondary='work_characters',
                              collection_class=set)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`WorkTrope`.
    work_tropes = relationship(lambda: WorkTrope,
                               cascade='delete, merge, save-update',
                               collection_class=set)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`Trope`.
    tropes = relationship(Trope, secondary='work_tropes',
                          collection_class=set)

    #: (:class:`datetime.datetime`) The date and time on which
    #: the record was created.
    created_at = Column(DateTime(timezone=True),
                        nullable=False,
                        default=now(),
                        index=True)

    __tablename__ = 'works'
    __repr_columns__ = [id]
    __mapper_args__ = {
        'polymorphic_identity': 'works',
    }


class WorkCharacter(Base):
    """Relationship between the character and the work.
    Describe that the character appeared in the work.
    """

    #: (:class:`int`) :class:`Work.id` of :attr:`work`.
    work_id = Column(Integer, ForeignKey(Work.id), primary_key=True)

    #: (:class:`Work`) The work in which the :attr:`character` appeared.
    work = relationship(Work)

    #: (:class:`int`) :class:`Character.id` of :attr:`character`.
    character_id = Column(Integer, ForeignKey(Character.id), primary_key=True)

    #: (:class:`Character`) The character that appeared in the :attr:`work`.
    character = relationship(Character)

    #: (:class:`datetime.datetime`) The date and time on which
    #: the record was created.
    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=now())

    __tablename__ = 'work_characters'
    __repr_columns__ = work_id, character_id


class WorkFranchise(Base):
    """Relationship between the work and the Franchise."""

    #: (:class:`int`) :class:`Work.id` of :attr:`work`.
    work_id = Column(Integer, ForeignKey(Work.id), primary_key=True)

    #: (:class:`Work`) The work that belongs to the :attr:`franchise`.
    work = relationship(Work)

    #: (:class:`int`) :class:`Franchise.id` of :attr:`franchise`.
    franchise_id = Column(Integer, ForeignKey(Franchise.id), primary_key=True)

    #: (:class:`Franchise`) The franchise that the :attr:`work` belongs to.
    franchise = relationship(Franchise)

    #: (:class:`datetime.datetime`) The date and time on which
    #: the record was created.
    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=now())

    __tablename__ = 'work_franchises'
    __repr_columns__ = work_id, franchise_id


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


class WorkTrope(Base):
    """Work - Trope"""

    #: (:class:`int`) :class:`Work.id` of :attr:`work`.
    work_id = Column(Integer, ForeignKey(Work.id), primary_key=True)

    #: (:class:`int`) :class:`Trope.id` of :attr:`trope`.
    trope_id = Column(Integer, ForeignKey(Trope.id), primary_key=True)

    #: (:class:`Work`) The work.
    work = relationship(Work)

    #: (:class:`Trope`) The trope.
    trope = relationship(Trope)

    __tablename__ = 'work_tropes'
    __repr_columns__ = work_id, trope_id


class World(Nameable):
    """Fictional universe that is a self-consistent fictional setting
    with elements that differ from the real world,
    for example *Middle-earth* and *Marvel Cinematic Universe*.
    """

    #: (:class:`int`) The primary key integer.
    id = Column(Integer, ForeignKey(Nameable.id), primary_key=True)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`Franchise`\ s that belong the world.
    franchises = relationship(Franchise,
                              foreign_keys=[id],
                              collection_class=set)

    #: (:class:`datetime.datetime`) The date and time on which
    #: the record was created.
    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=now())

    __tablename__ = 'worlds'
    __repr_columns__ = [id]
    __mapper_args__ = {
        'polymorphic_identity': 'worlds',
    }


prevent_discriminator_from_changing(Franchise.type)
prevent_discriminator_from_changing(Work.type)
prevent_discriminator_from_changing(World.type)
