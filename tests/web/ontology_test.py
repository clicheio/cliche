import datetime

from lxml.html import document_fromstring

from cliche.name import Name
from cliche.people import Person, Team
from cliche.sqltypes import HashableLocale as Locale
from ..web_utils import assert_contain_text
from cliche.work import Credit, Genre, Role, Work


def test_work_list(fx_session, fx_flask_client):
    # case 1: non-exists document
    rv = fx_flask_client.get('/work/')
    assert_contain_text('No contents here now.', 'tbody>tr>td', rv.data)

    # case 2: add document
    work = Work(media_type='Literature')
    work.names.update({
        Name(nameable=work,
             name='Story of Your Life',
             locale=Locale.parse('en_US'))
    })

    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/')
    assert_contain_text('Story of Your Life', 'tbody>tr>td', rv.data)


def test_work_page(fx_session, fx_flask_client):
    # case 1: non-exists document
    rv = fx_flask_client.get('/work/1/')
    assert rv.status_code == 404

    # case 2: add document
    work = Work(media_type='Literature')
    work.names.update({
        Name(nameable=work,
             name='Story of Your Life',
             locale=Locale.parse('en_US'))
    })
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get(
        '/work/{}/'.format(work.canonical_name(Locale.parse('en_US')))
    )
    assert_contain_text('Story of Your Life', 'h1', rv.data)
    assert_contain_text('Story of Your Life', 'tr.name>td', rv.data)

    # case 3: set attributes
    work.published_at = datetime.date(2010, 10, 26)
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get(
        '/work/{}/'.format(work.canonical_name(Locale.parse('en_US')))
    )
    assert_contain_text('2010-10-26', 'tr.published_at>td', rv.data)

    work.genres.add(Genre(name='Short Stories'))
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get(
        '/work/{}/'.format(work.canonical_name(Locale.parse('en_US')))
    )
    assert_contain_text('Short Stories', 'tr.genres>td', rv.data)

    work.genres.add(Genre(name='SF'))
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get(
        '/work/{}/'.format(work.canonical_name(Locale.parse('en_US')))
    )
    assert_contain_text('Short Stories', 'tr.genres>td', rv.data)
    assert_contain_text('SF', 'tr.genres>td', rv.data)

    author = Person()
    author.names.update({
        Name(nameable=author,
             name='Ted Chiang',
             locale=Locale.parse('en_US'))
    })
    credit = Credit(person=author, work=work, role=Role.author)

    with fx_session.begin():
        fx_session.add(credit)

    rv = fx_flask_client.get(
        '/work/{}/'.format(work.canonical_name(Locale.parse('en_US')))
    )
    assert_contain_text('Ted Chiang', 'tr.credits>td>table>tbody>tr>td.name',
                        rv.data)
    assert_contain_text(Role.author.value,
                        'tr.credits>td>table>tbody>tr>td.role',
                        rv.data)

    assert document_fromstring(rv.data).xpath(
        '//tr/td[@class="name"]/a[text()="Ted Chiang"]'
        '/../../td[@class="role"]/a[text()="{}"]'.format(Role.author.value)
    )


def test_complex_credits(fx_session, fx_flask_client):
    """Data: http://www.animenewsnetwork.com/encyclopedia/anime.php?id=12376"""
    work = Work(media_type='Anime')
    work.names.update({
        Name(nameable=work,
             name='Fate/Zero',
             locale=Locale.parse('en_US'))
    })

    def make_with_name(cls, name):
        ins = cls()
        ins.names.update({
            Name(nameable=ins,
                 name=name,
                 locale=Locale.parse('en_US'))
        })
        return ins

    author_credit = Credit(person=make_with_name(Person, 'Akihiko Uda'),
                           work=work,
                           role=Role.author)
    ufotable = make_with_name(Team, 'ufotable')
    easter = make_with_name(Team, 'Studio Easter')
    artist_credits = [
        Credit(person=make_with_name(Person, "Aki In'yama"), work=work,
               role=Role.artist, team=ufotable),
        Credit(person=make_with_name(Person, 'Erika Okazaki'), work=work,
               role=Role.artist, team=easter),
        Credit(person=make_with_name(Person, 'Eun Kyung Seo'), work=work,
               role=Role.artist, team=easter),
        Credit(person=make_with_name(Person, 'Jeong Ji Kim'), work=work,
               role=Role.artist, team=ufotable)
    ]

    with fx_session.begin():
        fx_session.add(work)
        fx_session.add(author_credit)
        fx_session.add_all(artist_credits)

    rv = fx_flask_client.get(
        '/work/{}/'.format(work.canonical_name(Locale.parse('en_US')))
    )
    assert document_fromstring(rv.data).xpath(
        '//tr/td[@class="name"]/a[text()="Akihiko Uda"]'
        '/../../td[@class="role"]/a[text()="{}"]'.format(Role.author.value)
    )

    assert document_fromstring(rv.data).xpath(
        '//tr/td[@class="name"]/a[text()="Aki In\'yama"]'
        '/../../td[@class="team"]/a[text()="ufotable"]'
        '/../../td[@class="role"]/a[text()="{}"]'.format(Role.artist.value)
    )
    assert document_fromstring(rv.data).xpath(
        '//tr/td[@class="name"]/a[text()="Jeong Ji Kim"]'
        '/../../td[@class="role"]/a[text()="{}"]'.format(Role.artist.value)
    )
    assert len(document_fromstring(rv.data).xpath(
        '//tr/td[@class="name"]/a[text()="Jeong Ji Kim"]'
        '/../../td')) == 2

    assert document_fromstring(rv.data).xpath(
        '//tr/td[@class="name"]/a[text()="Erika Okazaki"]'
        '/../../td[@class="team"]/a[text()="Studio Easter"]'
        '/../../td[@class="role"]/a[text()="{}"]'.format(Role.artist.value)
    )
    assert document_fromstring(rv.data).xpath(
        '//tr/td[@class="name"]/a[text()="Eun Kyung Seo"]'
        '/../../td[@class="role"]/a[text()="{}"]'.format(Role.artist.value)
    )
    assert len(document_fromstring(rv.data).xpath(
        '//tr/td[@class="name"]/a[text()="Eun Kyung Seo"]'
        '/../../td')) == 2
