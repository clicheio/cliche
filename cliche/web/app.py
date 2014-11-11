""":mod:`cliche.web.app` --- Flask application object
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import datetime
import urllib.parse

from flask import Flask, current_app, g, render_template
from flask import session as flask_session
from flask_oauthlib.client import OAuth

from ..user import User
from .db import setup_session
from .db import session as sa_session
from .ontology import ontology
from .social.oauth import OAuthVendorConverter, oauth_app
from .user import user_app


__all__ = 'app', 'check_login_status', 'index'


#: (:class:`flask.Flask`) The Flask application object.
app = Flask(__name__, template_folder='templates')
oauth = OAuth()

setup_session(app)
oauth.init_app(app)

app.url_map.converters['oauth_vendor'] = OAuthVendorConverter

app.register_blueprint(ontology)
app.register_blueprint(user_app)
app.register_blueprint(oauth_app)


@app.route('/')
def index():
    """Cliche.io web index page."""
    return render_template('index.html')


@app.before_request
def check_login_status():
    """Check he/she logged and expired."""
    g.user = None
    try:
        logged_id = flask_session['logged_id']
    except KeyError:
        return
    now = g.get('test_now', datetime.datetime.utcnow())
    elapsed_time = now - flask_session['logged_time']
    if elapsed_time <= current_app.config['LOGIN_EXPIRATION_INTERVAL']:
        flask_session['logged_time'] = now

        g.user = sa_session.query(User).get(logged_id)
        return

    del flask_session['logged_id']
    del flask_session['logged_time']


@app.context_processor
def template_processor():
    def make_public_sentry_dsn():
        sentry_dsn = app.config.get('SENTRY_DSN', None)
        if sentry_dsn:
            parsed_dsn = urllib.parse.urlparse(sentry_dsn)
            new_dsn = (
                parsed_dsn.scheme,
                '{}@{}'.format(parsed_dsn.username, parsed_dsn.hostname),
                parsed_dsn.path,
                parsed_dsn.params,
                parsed_dsn.query,
                parsed_dsn.fragment,
            )
            return urllib.parse.ParseResult(*new_dsn).geturl()

    return dict(make_public_sentry_dsn=make_public_sentry_dsn)


@app.after_request
def add_login_header(response):
    """Add login header if he/she logged."""
    if g.user:
        response.headers['X-Cliche-Login-User-Id'] = g.user.id
    return response
