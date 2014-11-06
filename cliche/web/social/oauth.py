""":mod:`cliche.web.social.twitter` --- Twitter Support
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Cliche provides Twitter login/join to use our service.
It widely uses Flask-OAuthlib_ as its OAuth framework.

.. _Flask-OAuthlib: https://flask-oauthlib.readthedocs.org/

"""
import collections
import datetime
import enum

from flask import Blueprint, flash, redirect, request, url_for
from flask import session as flask_session
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.routing import BaseConverter, ValidationError

from ...credentials import TwitterCredential
from ..db import session as sa_session
from .provider import twitter
from ...user import User


__all__ = ('OAuthVendorConverter', 'Vendor', 'Version', 'login', 'oauth_app',
           'oauth_authorized', 'vendors')


oauth_app = Blueprint('oauth', __name__)

Vendor = collections.namedtuple(
    'Vendor',
    ['name', 'credential_table', 'oauth_version', 'oauth_client', 'key_names']
)


class Version(enum.Enum):
    oauth1 = 1
    oauth2 = 2


vendors = [
    Vendor('twitter', TwitterCredential, Version.oauth1, twitter,
           ('screen_name', 'user_id'))
]


@oauth_app.route('/login/<oauth_vendor:vendor>/')
def login(vendor):
    """Login."""
    if 'logged_id' in flask_session:
        return redirect(url_for('index'))

    return vendor.oauth_client.authorize(
        callback=url_for(
            '.oauth_authorized',
            vendor=vendor,
            next=request.args.get('next') or request.referrer or None
        )
    )


@oauth_app.route('/oauth-authorized/<oauth_vendor:vendor>/')
def oauth_authorized(vendor):
    """Authorized OAuth and login or join with social account."""
    if 'logged_id' in flask_session:
        return redirect(url_for('index'))

    next_url = request.args.get('next') or url_for('index')

    name_key, id_key = vendor.key_names

    resp = vendor.oauth_client.authorized_response()
    if resp is None:
        flash('You denied the request to sign in.')
        return redirect(next_url)

    now = datetime.datetime.utcnow()

    user_id = resp[id_key]
    user_name = resp[name_key]

    with sa_session.begin():
        try:
            social = sa_session.query(vendor.credential_table) \
                               .filter_by(identifier=user_id) \
                               .one()
        except NoResultFound:
            social = make_account(vendor.credential_table, user_name, user_id)
            sa_session.add(social)

        if vendor.oauth_version == Version.oauth1:
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


class OAuthVendorConverter(BaseConverter):

    def __init__(self, url_map):
        super(OAuthVendorConverter, self).__init__(url_map)
        self.regex = '[^/]+'

    def to_python(self, value):
        for v in vendors:
            if v.name == value:
                return v
        raise ValidationError()

    def to_url(self, value):
        if type(value) == Vendor:
            return value.name
        else:
            return value
