# -*- coding: utf-8 -*-
""":mod:`cliche.web.ontology` --- Ontology web views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Cliche provides ontology web pages to use our database.
It widely uses Flask_ as its web framework.

.. _Flask: http://flask.pocoo.org/

"""
import itertools

from cliche.sqltypes import HashableLocale as Locale
from flask import Blueprint, abort, render_template
from sqlalchemy.orm.exc import NoResultFound

from .db import session
from ..work import Credit, Work

ontology = Blueprint('ontology', __name__,
                     template_folder='templates/ontology/')


@ontology.route('/')
def index():
    """The root page. Currently no contents preserved yet."""
    return 'Hello cliche!'


@ontology.route('/work/')
def list_():
    """A list of id-name pairs of works."""
    res = session.query(Work.id,
                        Work.canonical_name(Locale.parse('en_US'))
                            .label('canonical_name')) \
                 .order_by('canonical_name') \
                 .all()
    work_list = [(id, title) for id, title in res]

    return render_template(
        'work_list.html',
        work_list=work_list
    )


@ontology.route('/work/<path:id>/')
def page(id):
    """More detailed data of a work."""
    try:
        work = session.query(Work).filter_by(id=id).one()
    except NoResultFound:
        abort(404)
    credits = session.query(Credit) \
                     .filter_by(work=work) \
                     .order_by(Credit.team_id)
    grouped_credits = [
        (team_id, list(group))
        for team_id, group in itertools.groupby(credits, lambda c: c.team_id)
    ]

    return render_template(
        'page_work.html',
        title=work.canonical_name(Locale.parse('en_US')),
        locale=Locale.parse('en_US'),
        work=work,
        grouped_credits=grouped_credits
    )
