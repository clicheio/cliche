import datetime

from cliche.work import Award, Genre, Team, Work


def test_index(fx_session, fx_flask_client):
    rv = fx_flask_client.get('/')
    assert 'Hello cliche!' in str(rv.data)


def test_work_list(fx_session, fx_flask_client):
    # case 1: non-exists type_
    rv = fx_flask_client.get('/no_exists_type')
    assert rv.status_code == 404

    # case 2: non-exists document
    rv = fx_flask_client.get('/work')
    assert 'No contents here now.' in str(rv.data)

    # case 3: add document
    work = Work(name='test title')

    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work')
    assert 'test title' in str(rv.data)


def test_work_page(fx_session, fx_flask_client):
    # case 1: non-exists type_
    rv = fx_flask_client.get('/no_exists_type')
    assert rv.status_code == 404

    # case 2: non-exists document
    rv = fx_flask_client.get('/work/test')
    assert rv.status_code == 404

    # case 3: add document
    work = Work(name='test')

    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/test')
    assert 'test</h1>' in str(rv.data)

    # case 4: set attributes
    work.published_at = datetime.date(2014, 7, 1)
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/test')
    assert '2014-07-01' in str(rv.data)

    work.number_of_pages = 4321
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/test')
    assert '4321' in str(rv.data)

    work.isbn = '1234567890'
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/test')
    assert '1234567890' in str(rv.data)

    work.team = Team(name='MUSE')
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/test')
    assert 'MUSE' in str(rv.data)

    work.awards.add(Award(name='Bob-sang'))
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/test')
    assert 'Bob-sang' in str(rv.data)

    work.awards.add(Award(name='Sura-sang'))
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/test')
    assert 'Bob-sang' in str(rv.data)
    assert 'Sura-sang' in str(rv.data)

    work.genres.add(Genre(name='Horror'))
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/test')
    assert 'Horror' in str(rv.data)

    work.genres.add(Genre(name='SF'))
    with fx_session.begin():
        fx_session.add(work)

    rv = fx_flask_client.get('/work/test')
    assert 'Horror' in str(rv.data)
    assert 'SF' in str(rv.data)
