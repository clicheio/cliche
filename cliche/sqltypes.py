""":mod:`cliche.sqltypes` --- Collection of custom types for SQLAlchemy.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import enum
import uuid

from babel import Locale
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm.events import event
from sqlalchemy.sql.expression import func
from sqlalchemy.types import CHAR, Enum, SchemaType, String, TypeDecorator
from sqlalchemy.util.langhelpers import _symbol

__all__ = ('EnumType', 'HashableLocale', 'LocaleType',
           'prevent_discriminator_from_changing', 'prevent_instantiating',
           'UuidType')


def prevent_discriminator_from_changing(col):
    def set_discriminator(target, value, oldvalue, initiator):
        oldvalue_is_none = (
            oldvalue.__class__ != _symbol or oldvalue.name != 'NO_VALUE'
        )
        value_is_wrong = (
            value != target.__mapper_args__['polymorphic_identity']
        )
        if oldvalue_is_none or value_is_wrong:
            raise AttributeError('discriminator column cannot be changed')

    event.listen(col, 'set', set_discriminator)


def prevent_instantiating(cls):
    def init_non_instantiable_cls(target, args, kwargs):
        raise Exception('{} cannot be instantiated'.format(target.__class__))

    event.listen(cls, 'init', init_non_instantiable_cls)


class EnumType(TypeDecorator, SchemaType):
    """Custom enum type to be used as :class:`enum.Enum`in Python standard
    library. It inherits :class:`sqlalchemy.types.SchemaType` since it
    requires schema-level DDL. PostgreSQL ENUM type defined in an Alembic
    script must be explicitly created/dropped.
    """

    impl = Enum

    def __init__(self, enum_class: enum.Enum, **kw):
        if not issubclass(enum_class, enum.Enum):
            raise TypeError('expected enum.Enum subtype')
        super().__init__(*(m.name for m in enum_class), **kw)
        self._enum_class = enum_class

    def process_bind_param(self, value, dialect):
        return value.name

    def process_result_value(self, value, dialect):
        return self._enum_class[value]

    def _set_parent(self, column):
        self.impl._set_parent(column)

    @property
    def python_type(self):
        return self._enum_class


class HashableLocale(Locale):
    """Hashable Locale"""

    def __hash__(self):
        return hash('{}_{}'.format(self.language, self.territory))


class LocaleType(TypeDecorator):
    """Custom locale type to be used as :class:`babel.Locale`."""

    impl = String

    def bind_processor(self, dialect):
        def process_bind_param(value):
            if not issubclass(value.__class__, Locale):
                raise TypeError('expected babel.Locale instance')
            return '{}_{}'.format(value.language, value.territory)
        return process_bind_param

    def result_processor(self, dialect, coltype):
        def process_result_value(value):
            if value is None:
                return value
            return HashableLocale.parse(value)
        return process_result_value

    class comparator_factory(TypeDecorator.Comparator):
        @property
        def language(self):
            return func.substr(self.expr, 1, 2)

        @property
        def territory(self):
            return func.substr(self.expr, 4, 2)


class UuidType(TypeDecorator):
    """Custom UUID type to be used as :class:`uuid.UUID`."""

    impl = CHAR

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def bind_processor(self, dialect):
        def process_bind_param(value):
            if value is None:
                return value
            if not isinstance(value, uuid.UUID):
                raise TypeError('expected uuid.UUID instance')

            if dialect.name == 'postgresql':
                return str(value)
            else:
                return '{0:032x}'.format(int(value))
        return process_bind_param

    def result_processor(self, dialect, coltype):
        def process_result_value(value):
            if value is None or isinstance(value, uuid.UUID):
                return value
            else:
                return uuid.UUID(value)
        return process_result_value
