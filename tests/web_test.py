import datetime
import urllib.parse

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


def test_raven_js_installed(fx_flask_client, fx_sentry_config):
    rv = fx_flask_client.get(get_url('index'))
    assert 'Raven.config(' in rv.data.decode('u8')


def test_raven_js_not_installed(fx_flask_client):
    """Without Sentry DSN, Raven-js must not set."""
    rv = fx_flask_client.get(get_url('index'))
    assert 'Raven.config(' not in rv.data.decode('u8')


def test_raven_js_config_dsn_without_secret_key(fx_flask_client,
                                                fx_sentry_config):
    dsn = urllib.parse.urlparse(fx_sentry_config)
    new_dsn = urllib.parse.ParseResult(dsn.scheme,
                                       '{}@{}'.format(dsn.username,
                                                      dsn.hostname),
                                       dsn.path,
                                       dsn.params,
                                       dsn.query,
                                       dsn.fragment).geturl()
    rv = fx_flask_client.get(get_url('index'))
    assert "Raven.config('{}'".format(new_dsn) in rv.data.decode('u8')
