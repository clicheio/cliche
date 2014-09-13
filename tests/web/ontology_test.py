import datetime

from lxml.html import document_fromstring

from cliche.work import Award, Genre, Work


def assert_contain_text(text, path, data):
    def traverse(elements):
        for element in elements:
            yield text in element.text_content()

    tree = document_fromstring(str(data)).xpath(path)
    assert tree
    assert any(traverse(tree))


def test_index(fx_session, fx_flask_client):
    rv = fx_flask_client.get('/')
    assert 'Hello cliche!' in str(rv.data)


def test_work_list(fx_session, fx_flask_client):
    # case 1: non-exists document
    rv = fx_flask_client.get('/work/')
    assert_contain_text('No contents here now.', '//tbody/tr/td', rv.data)

    # case 2: add document
    work = Work(name='Story of Your Life')

    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/')
    assert_contain_text('Story of Your Life', '//tbody/tr/td/a', rv.data)


def test_work_page(fx_session, fx_flask_client):
    # case 1: non-exists document
    rv = fx_flask_client.get('/work/Story%20of%20Your%20Life/')
    assert rv.status_code == 404

    # case 2: add document
    work = Work(name='Story of Your Life')

    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/Story%20of%20Your%20Life/')
    assert_contain_text('Story of Your Life', '//h1', rv.data)

    # case 3: set attributes
    work.published_at = datetime.date(2010, 10, 26)
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/Story%20of%20Your%20Life/')
    assert_contain_text('2010-10-26', '//tbody/tr/td', rv.data)

    work.number_of_pages = 281
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/Story%20of%20Your%20Life/')
    assert_contain_text('281', '//tbody/tr/td', rv.data)

    work.isbn = '1931520720'
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/Story%20of%20Your%20Life/')
    assert_contain_text('1931520720', '//tbody/tr/td', rv.data)

    work.awards.add(Award(name='Nebula Award'))
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/Story%20of%20Your%20Life/')
    assert_contain_text('Nebula Award', '//tbody/tr/td/ul/li/a', rv.data)

    work.awards.add(Award(name='Sturgeon Award'))
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/Story%20of%20Your%20Life/')
    assert_contain_text('Nebula Award', '//tbody/tr/td/ul/li/a', rv.data)
    assert_contain_text('Sturgeon Award', '//tbody/tr/td/ul/li/a', rv.data)

    work.genres.add(Genre(name='Short Stories'))
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/Story%20of%20Your%20Life/')
    assert_contain_text('Short Stories', '//tbody/tr/td/ul/li/a', rv.data)

    work.genres.add(Genre(name='SF'))
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/Story%20of%20Your%20Life/')
    assert_contain_text('Short Stories', '//tbody/tr/td/ul/li/a', rv.data)
    assert_contain_text('SF', '//tbody/tr/td/ul/li/a', rv.data)
