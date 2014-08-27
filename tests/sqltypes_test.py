import enum

from sqlalchemy.schema import Column
from sqlalchemy.types import Integer

from cliche.sqltypes import EnumType
from cliche.orm import Base


class Color(enum.Enum):

    red = 1
    green = 2
    blue = 3


class ColorTable(Base):

    __tablename__ = 'color_table'

    id = Column(Integer, primary_key=True)
    test_col = Column(EnumType(Color))


def test_enum_type(fx_session):
    red_obj = ColorTable(test_col=Color.red)
    green_obj = ColorTable(test_col=Color.green)
    blue_obj = ColorTable(test_col=Color.blue)
    fx_session.add(red_obj)
    fx_session.add(green_obj)
    fx_session.add(blue_obj)
    fx_session.flush()
    result_obj = fx_session.query(ColorTable) \
                           .filter(ColorTable.test_col == Color.green) \
                           .one()
    assert green_obj is result_obj
