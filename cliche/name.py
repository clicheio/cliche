""":mod:`cliche.title` --- Enable one or more names or titles.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from sqlalchemy.ext.hybrid import hybrid_method
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.sql.expression import select
from sqlalchemy.types import Integer, String

from .orm import Base
from .sqltypes import LocaleType

__all__ = ('Nameable', 'Name')


class Name(Base):
    """The name or title of an nameable instance."""

    #: (:class:`int`) :class:`Nameable.id` of :attr:`nameable`.
    nameable_id = Column(Integer,
                         ForeignKey('nameables.id'),
                         primary_key=True)

    #: (:class:`Nameable`) The nameable instance that has :attr:`name`.
    nameable = relationship('Nameable')

    #: (:class:'str') The title of :attr:`nameable`.
    name = Column(String, primary_key=True)

    #: (:class:`int`) The number of references to the title.
    reference_count = Column(Integer, default=0)

    #: (:class:`cliche.sqltypes.LocaleType`) The locale of :attr:`title`.
    locale = Column(LocaleType, primary_key=True)

    __tablename__ = 'names'
    __repr_columns__ = nameable_id, name, locale


class Nameable(Base):
    """This mapped class is a abstract base class for all of mapped classes
    that could have multiple names. It enables the table of :class:`Name` to
    have a column which is a foreign key of any one of tables that has one or
    more names.
    """

    #: (:class:`int`) The primary key integer.
    id = Column(Integer, primary_key=True)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`cliche.name.Name`\ s that the object has.
    names = relationship(
        Name,
        cascade='delete, merge, save-update',
        collection_class=set
    )

    @hybrid_method
    def canonical_name(self, locale):
        def name_key(name):
            return (
                name.locale.language != locale.language,
                name.locale.territory != locale.territory,
                -name.reference_count,
                name.name
            )
        if(self.names):
            return min(self.names, key=name_key)
        else:
            return None

    @canonical_name.expression
    def canonical_name(cls, locale):
        return select(
            [Name.name],
            Name.nameable_id == Nameable.id,
            limit=1
        ).order_by(
            (Name.locale.language == locale.language).desc(),
            (Name.locale.territory == locale.territory).desc(),
            (Name.reference_count).desc(),
            (Name.name).asc()
        ).as_scalar()

    type = Column(String)

    __tablename__ = 'nameables'
    __repr_columns__ = [id]
    __mapper_args__ = {
        'polymorphic_identity': 'nameables',
        'polymorphic_on': type
    }
