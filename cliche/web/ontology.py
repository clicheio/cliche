# -*- coding: utf-8 -*-
""":mod:`cliche.web.ontology` --- Ontology web views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Cliche provides ontology web pages to use our database.
It widely uses Flask_ as its web framework.

.. _Flask: http://flask.pocoo.org/

"""
import itertools

from flask import Blueprint, abort, render_template
from sqlalchemy import func
from sqlalchemy.orm import aliased
from sqlalchemy.orm.exc import NoResultFound

from .db import session
from ..work import Credit, Title, Work

ontology = Blueprint('ontology', __name__,
                     template_folder='templates/ontology/')


def get_primary_title(work_id):
    max_reference_count = session.query(func.max(Title.reference_count)) \
                                 .filter(Title.work_id == work_id) \
                                 .scalar()
    title = session.query(Title.title) \
                   .filter(Title.work_id == work_id) \
                   .filter(Title.reference_count == max_reference_count) \
                   .first() \
                   .title
    return title


@ontology.route('/')
def index():
    """The root page. Currently no contents preserved yet."""
    return 'Hello cliche!'


@ontology.route('/work/')
def list_():
    """A list of id-name pairs of works."""
    w = aliased(Work)
    t = aliased(Title)
    res = session.query(w, t) \
                 .filter(w.id == t.work_id) \
                 .filter(t.reference_count ==
                         session.query(func.max(Title.reference_count))
                                .filter(Title.work_id == t.work_id)
                                .correlate(t)) \
                 .order_by(t.title) \
                 .all()
    work_list = [(work.id, title.title) for work, title in res]

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
        title=get_primary_title(id),
        work=work,
        grouped_credits=grouped_credits
    )
