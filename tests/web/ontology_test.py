import datetime

from cliche.work import Award, Genre, Team, Work


def test_index(fx_session, fx_flask_client):
    rv = fx_flask_client.get('/')
    assert 'Hello cliche!' in str(rv.data)


def test_work_list(fx_session, fx_flask_client):
    # case 1: non-exists document
    rv = fx_flask_client.get('/work/')
    assert 'No contents here now.' in str(rv.data)

    # case 2: add document
    work = Work(name='Story of Your Life')

    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/')
    assert 'Story of Your Life' in str(rv.data)


def test_work_page(fx_session, fx_flask_client):
    # case 1: non-exists document
    rv = fx_flask_client.get('/work/Story%20of%20Your%20Life/')
    assert rv.status_code == 404

    # case 2: add document
    work = Work(name='Story of Your Life')

    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/Story%20of%20Your%20Life/')
    assert 'Story of Your Life</h1>' in str(rv.data)

    # case 3: set attributes
    work.published_at = datetime.date(2010, 10, 26)
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/Story%20of%20Your%20Life/')
    assert '2010-10-26' in str(rv.data)

    work.number_of_pages = 281
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/Story%20of%20Your%20Life/')
    assert '281' in str(rv.data)

    work.isbn = '1931520720'
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/Story%20of%20Your%20Life/')
    assert '1931520720' in str(rv.data)

    work.team = Team(name='Ted Chiang')
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/Story%20of%20Your%20Life/')
    assert 'Ted Chiang' in str(rv.data)

    work.awards.add(Award(name='Nebula Award'))
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/Story%20of%20Your%20Life/')
    assert 'Nebula Award' in str(rv.data)

    work.awards.add(Award(name='Sturgeon Award'))
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/Story%20of%20Your%20Life/')
    assert 'Nebula Award' in str(rv.data)
    assert 'Sturgeon Award' in str(rv.data)

    work.genres.add(Genre(name='Short Stories'))
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/Story%20of%20Your%20Life/')
    assert 'Short Stories' in str(rv.data)

    work.genres.add(Genre(name='SF'))
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/Story%20of%20Your%20Life/')
    assert 'Short Stories' in str(rv.data)
    assert 'SF' in str(rv.data)
