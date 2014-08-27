""":mod:`cliche.sqltypes` --- Collection of custom types for SQLAlchemy.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import enum

from sqlalchemy.types import Enum, TypeDecorator

__all__ = 'EnumType',


class EnumType(TypeDecorator):
    """Enum type to be used as :class:`enum.Enum` in Python standard library.
    """

    impl = Enum

    def __init__(self, enum_class: enum.Enum, **kw):
        if issubclass(enum_class, enum.Enum):
            raise TypeError('expected enum.Enum subtype')
        super().__init__(*(m.name for m in enum_class), **kw)
        self._enum_class = enum_class

    def process_bind_param(self, value, dialect):
        return value.name

    def process_result_value(self, value, dialect):
        return self._enum_class[value]

    @property
    def python_type(self):
        return self._enum_class
