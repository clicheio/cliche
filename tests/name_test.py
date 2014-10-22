from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Integer, String

from cliche.name import Name, Nameable
from cliche.sqltypes import HashableLocale as Locale


class NameableNumber(Nameable):
    __tablename__ = 'nameable_numbers'
    __mapper_args__ = {
        'polymorphic_identity': 'nameable_numbers',
    }

    id = Column(Integer, ForeignKey(Nameable.id), primary_key=True)
    number = Column(Integer, primary_key=True)


class NameableString(Nameable):
    __tablename__ = 'nameable_strings'
    __mapper_args__ = {
        'polymorphic_identity': 'nameable_strings',
    }

    id = Column(Integer, ForeignKey(Nameable.id), primary_key=True)
    string = Column(String, primary_key=True)


def test_name(fx_session):
    kokr = Locale.parse('ko_KR')  # Korean (South Korea)
    enus = Locale.parse('en_US')  # English (United States)
    enca = Locale.parse('en_CA')  # English (Canada)
    esus = Locale.parse('es_US')  # Spanish (United States)
    jajp = Locale.parse('ja_JP')  # Japanese (Japan)

    one = NameableNumber(number=1)
    two = NameableNumber(number=2)
    mystr = NameableString(string='mystr')
    one.names.update({
        Name(nameable=one,
             name='하나',
             locale=kokr,
             reference_count=5),
        Name(nameable=one,
             name='일',
             locale=kokr,
             reference_count=20),
        Name(nameable=one,
             name='one',
             locale=enus,
             reference_count=15),
        Name(nameable=one,
             name='first',
             locale=enus,
             reference_count=10)
    })
    two.names.update({
        Name(nameable=two,
             name='이',
             locale=kokr,
             reference_count=25),
        Name(nameable=two,
             name='둘',
             locale=kokr,
             reference_count=25),
        Name(nameable=two,
             name='two',
             locale=enus,
             reference_count=5),
        Name(nameable=two,
             name='second',
             locale=enus,
             reference_count=5)
    })
    mystr.names.update({
        Name(nameable=mystr,
             name='my string',
             locale=enus,
             reference_count=3),
        Name(nameable=mystr,
             name='나의 문자열',
             locale=kokr,
             reference_count=4)
    })
    with fx_session.begin():
        fx_session.add_all([one, two, mystr])

    # Check whether all elements are properly inserted.
    assert fx_session.query(Nameable).count() == 3
    assert len(one.names) == 4
    assert len(two.names) == 4
    assert len(mystr.names) == 2
    assert fx_session.query(Name).count() == \
        len(one.names) + len(two.names) + len(mystr.names)
    assert {name.name for name in one.names} == {'일', '하나', 'first', 'one'}
    assert {name.locale for name in one.names} == {kokr, enus}

    def canonical_name_in_expr(nameable, *args):
        # Get the canonical name on the SQL expression side.
        # Its rationale is to test the hybrid method of Nameable in
        # expression behavior.
        nameable_class = nameable.__class__
        return fx_session.query(nameable_class.canonical_name(*args),
                                Nameable) \
                         .filter(Nameable.id == nameable.id) \
                         .scalar()

    # Find the canonical name with the same locale.
    # Expect the name which was the most referenced in the same locale.
    assert one.canonical_name(kokr).name == '일'
    assert canonical_name_in_expr(one, kokr) == '일'
    assert one.canonical_name(enus).name == 'one'
    assert canonical_name_in_expr(one, enus) == 'one'
    assert mystr.canonical_name(kokr).name == '나의 문자열'
    assert canonical_name_in_expr(mystr, kokr) == '나의 문자열'
    assert mystr.canonical_name(enus).name == 'my string'
    assert canonical_name_in_expr(mystr, enus) == 'my string'

    # Find the canonical name with different territory but the same language.
    # Expect the name which was the most referenced in the same language.
    assert one.canonical_name(enca).name == 'one'
    assert canonical_name_in_expr(one, enca) == 'one'

    # Find the canonical name with different language but the same territory.
    # Expect the name which was the most referenced in the same territory.
    assert one.canonical_name(esus).name == 'one'
    assert canonical_name_in_expr(one, esus) == 'one'

    # Find the canonical name with a entirely different locale.
    # Expect the name which was the most referenced regardless of a locale.
    assert one.canonical_name(jajp).name == '일'
    assert canonical_name_in_expr(one, jajp) == '일'

    # Find the canonical names when there are two or more candidates
    # (the same number of reference count and locale) for the canonical name.
    # Expect lexicographically earlier one.
    assert two.canonical_name(kokr).name == '둘'
    assert canonical_name_in_expr(two, kokr) == '둘'
    assert two.canonical_name(enus).name == 'second'
    assert canonical_name_in_expr(two, enus) == 'second'

    # Try to find the canonical name of nameable instance
    # which doesn't have any name. Expect None value.
    with fx_session.begin():
        for name in one.names:
            fx_session.delete(name)
        for name in mystr.names:
            fx_session.delete(name)
    assert not one.canonical_name(kokr)
    assert not canonical_name_in_expr(one, kokr)
    assert not mystr.canonical_name(enus)
    assert not canonical_name_in_expr(mystr, enus)

    # Test on cascade deletion
    two_id = two.id
    fx_session.delete(two)
    assert fx_session.query(Name).filter_by(nameable_id=two_id).count() == 0

    # Try to create Nameable directly. Expect to rasie a exception.
    try:
        Nameable()
        assert False
    except Exception:
        pass
