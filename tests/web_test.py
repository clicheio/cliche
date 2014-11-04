import datetime

from cliche.user import User
from .web_utils import assert_contain_text, get_url


def test_index(fx_flask_client):
    rv = fx_flask_client.get(get_url('index'))
    assert_contain_text('Cliche.io', 'h1', rv.data)


def test_login_expire(fx_session, fx_flask_client):
    user = User(name='cliche.io')
    with fx_session.begin():
        fx_session.add(user)

    with fx_flask_client.session_transaction() as sess:
        sess['logged_id'] = user.id
        sess['logged_time'] = datetime.datetime.utcnow() - \
            datetime.timedelta(hours=1)

    rv = fx_flask_client.get(get_url('index'))
    assert not rv.headers.get('X-Cliche-Login-User-Id', None)


def test_login_renewal(fx_session, fx_flask_client):
    user = User(name='cliche.io')
    with fx_session.begin():
        fx_session.add(user)

    with fx_flask_client.session_transaction() as sess:
        sess['logged_id'] = user.id
        sess['logged_time'] = datetime.datetime.utcnow() - \
            datetime.timedelta(minutes=59)

    rv = fx_flask_client.get(get_url('index'))
    assert rv.headers['X-Cliche-Login-User-Id'] == str(user.id)
