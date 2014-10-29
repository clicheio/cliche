""":mod:`cliche.web.social.twitter` --- Twitter Support
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Cliche provides Twitter login/join to use our service.
It widely uses Flask-OAuthlib_ as its OAuth framework.

.. _Flask-OAuthlib: https://flask-oauthlib.readthedocs.org/

"""

import datetime
import enum

from flask import Blueprint, flash, redirect, request, url_for
from flask import session as flask_session
from sqlalchemy.orm.exc import NoResultFound

from ...credentials import TwitterCredential
from ..db import session as sa_session
from .provider import twitter
from ...user import User


__all__ = ('login', 'oauth_app', 'oauth_authorized', 'vendors', 'version')


oauth_app = Blueprint('oauth', __name__)


class version(enum.Enum):
    oauth1 = 1
    oauth2 = 2


vendors = dict(
    twitter=(TwitterCredential, version.oauth1, twitter,
             ('screen_name', 'user_id'))
)


@oauth_app.route('/login/<string:vendor_name>/')
def login(vendor_name):
    """Login."""
    if 'logged_id' in flask_session:
        return redirect(url_for('index'))

    try:
        oauth_client = vendors.get(vendor_name, None)[2]
    except (KeyError, TypeError):
        flash('Unknown vendor name.')
        return redirect(url_for('index'))

    return oauth_client.authorize(
        callback=url_for(
            '.oauth_authorized',
            vendor_name=vendor_name,
            next=request.args.get('next') or request.referrer or None
        )
    )


@oauth_app.route('/oauth-authorized/<string:vendor_name>/')
def oauth_authorized(vendor_name):
    """Authorized OAuth and login or join with social account."""
    if 'logged_id' in flask_session:
        return redirect(url_for('index'))

    next_url = request.args.get('next') or url_for('index')

    try:
        credential_table, oauth_version, oauth_client, keys = \
            vendors[vendor_name]
    except KeyError:
        flash('Unknown vendor name.')
        return redirect(url_for('index'))

    name_key, id_key = keys

    resp = oauth_client.authorized_response()
    if resp is None:
        flash('You denied the request to sign in.')
        return redirect(next_url)

    now = datetime.datetime.utcnow()

    user_id = resp[id_key]
    user_name = resp[name_key]

    with sa_session.begin():
        try:
            social = sa_session.query(credential_table) \
                               .filter_by(identifier=user_id) \
                               .one()
        except NoResultFound:
            social = make_account(credential_table, user_name, user_id)
            sa_session.add(social)

        if oauth_version == version.oauth1:
            social.token = resp['oauth_token']
            social.token_secret = resp['oauth_token_secret']

    flask_session['logged_id'] = social.user_id
    flask_session['logged_time'] = now

    flash('You were signed in as %s' % user_name)
    return redirect(next_url)


def make_account(credential_table, name, user_id):
    """Make account.

    :param response: OAuth authorize response.
    :return: User record was created.
    :rtype: :class:`cliche.user.User`

    """
    user = User(name=name)
    social_account = credential_table(user=user, identifier=user_id)
    return social_account
