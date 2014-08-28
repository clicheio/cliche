""":mod:`cliche.sqltypes` --- Collection of custom types for SQLAlchemy.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import enum

from sqlalchemy.types import Enum, SchemaType, TypeDecorator

__all__ = 'EnumType',


class EnumType(TypeDecorator, SchemaType):
    """Enum type to be used as :class:`enum.Enum` in Python standard library.
    It inherits :class:`sqlalchemy.types.SchemaType` since it requires
    schema-level DDL. PostgreSQL ENUM type must be explicitly created/dropped.
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
