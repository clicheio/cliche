""":mod:`cliche.web.social.provider` --- Social Support
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Cliche provides Twitter login/join to use our service.
It widely uses Flask-OAuthlib_ as its OAuth framework.

.. _Flask-OAuthlib: https://flask-oauthlib.readthedocs.org/

"""

from flask import session
from flask_oauthlib.client import OAuth

__all__ = 'oauth', 'twitter',

#: (:class:`flask_oauthlib.client.OAuth`) OAuth client.
oauth = OAuth()

#: Twitter OAuth client.
twitter = oauth.remote_app(
    'twitter',
    base_url='https://api.twitter.com/1/',
    request_token_url='https://api.twitter.com/oauth/request_token',
    access_token_url='https://api.twitter.com/oauth/access_token',
    authorize_url='https://api.twitter.com/oauth/authenticate',
    app_key='TWITTER'
)


@twitter.tokengetter
def get_token(token=None):
    """Get token."""
    return session.get('twitter_token')
