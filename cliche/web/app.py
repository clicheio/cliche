""":mod:`cliche.web.app` --- Flask application object
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import datetime
import urllib.parse
import logging

from flask import Flask, current_app, g, render_template
from flask import session as flask_session
from flask_oauthlib.client import OAuth
from raven.contrib.flask import Sentry

from ..user import User
from .adv_search import adv_search_bp
from .db import setup_session
from .db import session as sa_session
from .ontology import ontology
from .social.oauth import OAuthVendorConverter, oauth_app
from .user import user_app
from ..work import Trope


__all__ = 'app', 'check_login_status', 'index', 'setup_sentry'


#: (:class:`flask.Flask`) The Flask application object.
app = Flask(__name__, template_folder='templates')
oauth = OAuth()

setup_session(app)
oauth.init_app(app)

app.url_map.converters['oauth_vendor'] = OAuthVendorConverter

app.register_blueprint(ontology)
app.register_blueprint(user_app)
app.register_blueprint(oauth_app)
app.register_blueprint(adv_search_bp, url_prefix='/adv_search')


def setup_sentry():
    if app.config['SENTRY_DSN']:
        app.config['SENTRY_INCLUDE_PATHS'] = ['cliche']
        return Sentry(
            app,
            dsn=app.config['SENTRY_DSN'],
            logging=True,
            level=logging.ERROR,
        )
    else:
        return None


def get_sentry() -> Sentry:
    """Get a sentry client.

    :returns: a sentry client
    :rtype: :class:`raven.contrib.flask.Sentry`

    """
    if not app.config['SENTRY_CLIENT']:
        app.config['SENTRY_CLIENT'] = setup_sentry()
    return app.config['SENTRY_CLIENT']


@app.route('/')
def index():
    """Cliche.io web index page."""
    tropes = sa_session.query(Trope).order_by(Trope.name)
    return render_template('index.html', tropes=tropes)


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
    sentry_dsn = app.config.get('SENTRY_DSN', None)
    public_sentry_dsn = None
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
        public_sentry_dsn = urllib.parse.ParseResult(*new_dsn).geturl()

    return dict(public_sentry_dsn=public_sentry_dsn)


@app.after_request
def add_login_header(response):
    """Add login header if he/she logged."""
    if g.user:
        response.headers['X-Cliche-Login-User-Id'] = g.user.id
    return response
