""":mod:`cliche.web.user` --- User web views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Cliche provides user web pages to use our database.
It widely uses Flask_ as its web framework.

.. _Flask: http://flask.pocoo.org/

"""
from flask import Blueprint, flash, redirect, request, session, url_for


__all__ = 'logout', 'user_app',

user_app = Blueprint('user', __name__)


@user_app.route('/logout/')
def logout():
    """Logout."""
    try:
        del session['logged_id']
        del session['logged_time']
    except KeyError:
        pass

    flash('You were logged out.', 'success')

    next_url = request.referrer or url_for('index')
    return redirect(next_url)
