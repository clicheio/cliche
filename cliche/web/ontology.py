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
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from .db import session
from ..work import Credit, Work

ontology = Blueprint('ontology', __name__,
                     template_folder='templates/ontology/')


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


@ontology.route('/work/<path:title>/')
def page(title):
    """More detailed data of a work."""
    try:
        stmt = session.query(
            Work.id,
            Work.canonical_name(Locale.parse('en_US')).label('canonical_name')
        ).subquery()
        res = session.query(stmt.c.id, stmt.c.canonical_name) \
                     .filter(stmt.c.canonical_name == title) \
                     .one()
    except NoResultFound:
        abort(404)
    except MultipleResultsFound:
        # When there are works with the same canonical name,
        # the ambiguity should be solved in a appropriate way.
        abort(404)
    work = session.query(Work).filter_by(id=res.id).one()

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
