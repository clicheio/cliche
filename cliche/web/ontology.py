# -*- coding: utf-8 -*-

from flask import Blueprint, abort, render_template
import itertools
from sqlalchemy.orm.exc import NoResultFound

from .db import session
from ..work import Credit, Work

ontology = Blueprint('ontology', __name__,
                     template_folder='templates/ontology/')


@ontology.route('/')
def index():
    return 'Hello cliche!'


@ontology.route('/work/')
def list_():
    names = [
        name
        for name, in session.query(Work.name).order_by(Work.name)
    ]
    return render_template(
        'work_list.html',
        work_list=names
    )


@ontology.route('/work/<path:title>/')
def page(title):
    try:
        work = session.query(Work).filter_by(name=title).one()
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
        title=title,
        work=work,
        grouped_credits=grouped_credits
    )
