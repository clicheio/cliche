import datetime

from cliche.user import User
from ..web_utils import assert_contain_text, get_url


def test_logout_logged_user(fx_session, fx_flask_client):
    user = User(name='cliche.io')
    with fx_session.begin():
        fx_session.add(user)

    with fx_flask_client.session_transaction() as sess:
        sess['logged_id'] = user.id
        sess['logged_time'] = datetime.datetime.utcnow()

    rv = fx_flask_client.get(get_url('user.logout'))
    assert rv.status_code == 302

    rv = fx_flask_client.get(get_url('index'))
    assert_contain_text('You were logged out.', 'ul.flash>li', rv.data)


def test_logout_non_logged_user(fx_flask_client):
    rv = fx_flask_client.get(get_url('user.logout'))
    assert rv.status_code == 302

    rv = fx_flask_client.get(get_url('index'))
    assert_contain_text('You were logged out.', 'ul.flash>li', rv.data)
