import enum

from babel import Locale
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Integer, String

from cliche.sqltypes import (EnumType, LocaleType,
                             prevent_discriminator_from_changing,
                             prevent_instantiating)
from cliche.orm import Base


class Color(enum.Enum):
    red = 1
    green = 2
    blue = 3


class ColorTable(Base):
    __tablename__ = 'color_table'

    id = Column(Integer, primary_key=True)
    color = Column(EnumType(Color, name='color'))


class LocaleTable(Base):
    __tablename__ = 'locale_table'

    id = Column(Integer, primary_key=True)
    locale = Column(LocaleType())


def test_enum_type(fx_session):
    red_obj = ColorTable(color=Color.red)
    green_obj = ColorTable(color=Color.green)
    blue_obj = ColorTable(color=Color.blue)
    fx_session.add(red_obj)
    fx_session.add(green_obj)
    fx_session.add(blue_obj)
    fx_session.flush()
    result_obj = fx_session.query(ColorTable) \
                           .filter(ColorTable.color == Color.green) \
                           .one()
    assert green_obj is result_obj


def test_locale_type(fx_session):
    en_us = LocaleTable(locale=Locale.parse('en_US'))
    de_de = LocaleTable(locale=Locale.parse('de_DE'))
    ko_kr = LocaleTable(locale=Locale.parse('ko_KR'))
    with fx_session.begin():
        fx_session.add_all([en_us, de_de, ko_kr])
    result = fx_session.query(LocaleTable) \
                       .filter(LocaleTable.locale == Locale.parse('de_DE')) \
                       .one()
    assert result.locale == Locale.parse('de_DE')


class Employee(Base):
    __tablename__ = 'employee'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    type = Column(String(50), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'employee',
        'polymorphic_on': type
    }


class Engineer(Employee):
    __tablename__ = 'engineer'
    id = Column(Integer, ForeignKey('employee.id'), primary_key=True)
    engineer_name = Column(String(30))

    __mapper_args__ = {
        'polymorphic_identity': 'engineer',
    }


class Manager(Employee):
    __tablename__ = 'manager'
    id = Column(Integer, ForeignKey('employee.id'), primary_key=True)
    manager_name = Column(String(30))

    __mapper_args__ = {
        'polymorphic_identity': 'manager',
    }


prevent_discriminator_from_changing(Engineer.type)
prevent_discriminator_from_changing(Manager.type)
prevent_instantiating(Employee)


def test_prevent_instantiating():
    try:
        Employee(name='kim')
        assert False
    except Exception:
        pass


def test_prevent_discriminator_from_changing(fx_session):
    try:
        Engineer(name='kim', type='changing_manually')
        assert False
    except AttributeError:
        pass

    eng = Engineer(name='kim', engineer_name='sw')
    try:
        eng.type = 'changing_manually'
        assert False
    except AttributeError:
        pass

    with fx_session.begin():
        fx_session.add(eng)
    assert eng.type == 'engineer'
