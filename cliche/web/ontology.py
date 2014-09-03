# -*- coding: utf-8 -*-

from flask import Blueprint, abort, render_template
from sqlalchemy.orm.exc import NoResultFound

from .db import session
from ..work import Work

ontology = Blueprint('ontology', __name__,
                     template_folder='templates/ontology/')


@ontology.route('/')
def index():
    return 'Hello cliche!'


@ontology.route('/work/')
def list_():
    res = [
        line[0]
        for line in session.query(Work.name).order_by(Work.name)
    ]
    return render_template(
        'list.html',
        page_title='cliche.io - list of Work',
        type='Work',
        list=res
    )


@ontology.route('/work/<path:title>/')
def page(title):
    try:
        res = session.query(Work).filter(Work.name == title).one()
    except NoResultFound:
        abort(404)
    return render_template(
        'page_work.html',
        page_title='cliche.io - contents of ' + title,
        type='Work',
        title=title,
        res=res
    )
