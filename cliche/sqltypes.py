""":mod:`cliche.sqltypes` --- Collection of custom types for SQLAlchemy.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import enum

from babel import Locale
from sqlalchemy.types import Enum, SchemaType, String, TypeDecorator

__all__ = 'EnumType', 'LocaleType'


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


class LocaleType(TypeDecorator):
    """Custom locale type to be used as :class:`babel.Locale`."""

    impl = String

    def process_bind_param(self, value, dialect):
        if not isinstance(value, Locale):
            raise TypeError('expected babel.Locale instance')
        return '{}_{}'.format(value.language, value.territory)

    def process_result_value(self, value, dialect):
        return Locale.parse(value)
