import datetime

from cliche.credentials import TwitterCredential
from cliche.user import User
from cliche.web.social.oauth import Vendor, version
from ...web_utils import assert_contain_text, get_url


class FakeProvider:

    def __init__(self, res):
        self.res = res

    def authorized_response(self):
        return self.res


def test_undefined_vendor_login(fx_flask_client, fx_twitter_config):
    rv = fx_flask_client.get(get_url('oauth.login', vendor='naver'))
    assert rv.status_code == 404


def test_login_who_logged(fx_session, fx_flask_client, fx_twitter_config):
    user = User(name='cliche.io')
    with fx_session.begin():
        fx_session.add(user)

    with fx_flask_client.session_transaction() as sess:
        sess['logged_id'] = user.id
        sess['logged_time'] = datetime.datetime.utcnow()

    rv = fx_flask_client.get(get_url('oauth.login', vendor='twitter'))
    assert rv.status_code == 302


def test_twitter_login(fx_flask_client, fx_twitter_config):
    rv = fx_flask_client.get(get_url('oauth.login', vendor='twitter'))
    assert rv.status_code == 302


def test_undefined_vendor_authorize(fx_flask_client, fx_twitter_config):
    rv = fx_flask_client.get(get_url('oauth.oauth_authorized', vendor='naver'))
    assert rv.status_code == 404


def test_authorize_who_logged(fx_session, fx_flask_client, fx_twitter_config):
    user = User(name='cliche.io')
    with fx_session.begin():
        fx_session.add(user)

    with fx_flask_client.session_transaction() as sess:
        sess['logged_id'] = user.id
        sess['logged_time'] = datetime.datetime.utcnow()

    rv = fx_flask_client.get(get_url('oauth.oauth_authorized',
                                     vendor='twitter'))
    assert rv.status_code == 302


def test_twitter_authorize_failed(fx_flask_client,
                                  fx_twitter_config, monkeypatch):
    fake_vendors = [
        Vendor('twitter', TwitterCredential, version.oauth1,
               FakeProvider(None), ('screen_name', 'user_id'))
    ]

    monkeypatch.setattr('cliche.web.social.oauth.vendors', fake_vendors)

    rv = fx_flask_client.get(get_url('oauth.oauth_authorized',
                                     vendor='twitter'))
    assert rv.status_code == 302

    rv = fx_flask_client.get(get_url('index'))
    assert_contain_text('You denied the request to sign in.', 'ul.flush>li',
                        rv.data)


def test_twitter_authorize_new_id(fx_session, fx_flask_client,
                                  fx_twitter_config, monkeypatch):
    fake_res = dict(
        user_id='1234567890',
        screen_name='cliche.io',
        oauth_token='ASDFGHJKL:"',
        oauth_token_secret='QWERTYUIOP{}',
    )
    fake_vendors = [
        Vendor('twitter', TwitterCredential, version.oauth1,
               FakeProvider(fake_res), ('screen_name', 'user_id'))
    ]

    monkeypatch.setattr('cliche.web.social.oauth.vendors', fake_vendors)

    rv = fx_flask_client.get(get_url('oauth.oauth_authorized',
                                     vendor='twitter'))
    assert rv.status_code == 302

    created_user = fx_session.query(User).\
        filter(
            User.credentials.any(
                TwitterCredential.identifier == fake_res['user_id']
            )
        ).one()
    created_twitter_credential = fx_session.query(TwitterCredential).\
        filter_by(user=created_user).one()

    assert created_user.name == fake_res['screen_name']
    assert created_twitter_credential.token == fake_res['oauth_token']
    assert created_twitter_credential.token_secret == \
        fake_res['oauth_token_secret']

    rv = fx_flask_client.get(get_url('index'))
    rv.headers['X-Cliche-Login-User-Id'] == str(created_user.id)


def test_twitter_authorize_old_id(fx_session, fx_flask_client,
                                  fx_twitter_config, monkeypatch):
    # Make ID for test
    fake_old_res = dict(
        user_id='1234567890',
        screen_name='cliche.io',
        oauth_token='ASDFGHJKL:"',
        oauth_token_secret='QWERTYUIOP{}',
    )

    old_twitter_credential = TwitterCredential(
        identifier=fake_old_res['user_id'],
        token=fake_old_res['oauth_token'],
        token_secret=fake_old_res['oauth_token_secret']
    )
    old_user = User(name=fake_old_res['screen_name'],
                    credentials={old_twitter_credential})
    with fx_session.begin():
        fx_session.add(old_user)

    fake_new_res = dict(
        user_id='1234567890',
        screen_name='cliche.io',
        oauth_token='":LKJHGFDSA',
        oauth_token_secret='}{POIUYTREWQ',
    )
    fake_new_vendors = [
        Vendor('twitter', TwitterCredential, version.oauth1,
               FakeProvider(fake_new_res), ('screen_name', 'user_id'))
    ]

    monkeypatch.setattr('cliche.web.social.oauth.vendors', fake_new_vendors)

    rv = fx_flask_client.get(get_url('oauth.oauth_authorized',
                                     vendor='twitter'))
    assert rv.status_code == 302

    created_new_user = fx_session.query(User). \
        filter(
            User.credentials.any(
                TwitterCredential.identifier == fake_new_res['user_id']
            )
        ).one()
    fx_session.expire(created_new_user)

    created_new_twitter_credential = fx_session.query(TwitterCredential). \
        filter_by(user=created_new_user).one()
    fx_session.expire(created_new_twitter_credential)

    assert old_user == created_new_user
    assert old_twitter_credential == created_new_twitter_credential
    assert created_new_user.name == fake_old_res['screen_name']
    assert created_new_twitter_credential.token == fake_new_res['oauth_token']
    assert created_new_twitter_credential.token_secret == \
        fake_new_res['oauth_token_secret']
