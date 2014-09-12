import datetime

from lxml.etree import _ElementUnicodeResult
from lxml.html import document_fromstring

from cliche.work import Award, Genre, Team, Work


def contain_text(text, path, data):
    def inspect(haystack):
        return haystack is not None and text in haystack

    def traverse(tree):
        for element in tree:
            if isinstance(element, _ElementUnicodeResult):
                yield inspect(element)
            else:
                yield inspect(element.text)

    tree = document_fromstring(str(data)).xpath(path)
    if not tree:
        return False

    return any(traverse(tree))


def test_index(fx_session, fx_flask_client):
    rv = fx_flask_client.get('/')
    assert 'Hello cliche!' in str(rv.data)


def test_work_list(fx_session, fx_flask_client):
    # case 1: non-exists document
    rv = fx_flask_client.get('/work/')
    assert contain_text('No contents here now.', '//tbody/tr/td', rv.data)

    # case 2: add document
    work = Work(name='Story of Your Life')

    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/')
    assert contain_text('Story of Your Life', '//tbody/tr/td/a', rv.data)


def test_work_page(fx_session, fx_flask_client):
    # case 1: non-exists document
    rv = fx_flask_client.get('/work/Story%20of%20Your%20Life/')
    assert rv.status_code == 404

    # case 2: add document
    work = Work(name='Story of Your Life')

    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/Story%20of%20Your%20Life/')
    assert contain_text('Story of Your Life', '//h1/text()', rv.data)

    # case 3: set attributes
    work.published_at = datetime.date(2010, 10, 26)
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/Story%20of%20Your%20Life/')
    assert contain_text('2010-10-26', '//tbody/tr/td', rv.data)

    work.number_of_pages = 281
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/Story%20of%20Your%20Life/')
    assert contain_text('281', '//tbody/tr/td', rv.data)

    work.isbn = '1931520720'
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/Story%20of%20Your%20Life/')
    assert contain_text('1931520720', '//tbody/tr/td', rv.data)

    work.team = Team(name='Ted Chiang')
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/Story%20of%20Your%20Life/')
    assert contain_text('Ted Chiang', '//tbody/tr/td/a', rv.data)

    work.awards.add(Award(name='Nebula Award'))
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/Story%20of%20Your%20Life/')
    assert contain_text('Nebula Award', '//tbody/tr/td/ul/li/a', rv.data)

    work.awards.add(Award(name='Sturgeon Award'))
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/Story%20of%20Your%20Life/')
    assert contain_text('Nebula Award', '//tbody/tr/td/ul/li/a', rv.data)
    assert contain_text('Sturgeon Award', '//tbody/tr/td/ul/li/a', rv.data)

    work.genres.add(Genre(name='Short Stories'))
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/Story%20of%20Your%20Life/')
    assert contain_text('Short Stories', '//tbody/tr/td/ul/li/a', rv.data)

    work.genres.add(Genre(name='SF'))
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/Story%20of%20Your%20Life/')
    assert contain_text('Short Stories', '//tbody/tr/td/ul/li/a', rv.data)
    assert contain_text('SF', '//tbody/tr/td/ul/li/a', rv.data)
