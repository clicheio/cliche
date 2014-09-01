# -*- coding: utf-8 -*-

from flask import Blueprint, abort, render_template
from sqlalchemy.orm.exc import NoResultFound

from .db import session
from ..work import Work

type_map = {
    # name, ORM Table class, field for total list
    'work': ('Work', Work, Work.name)
}

ontology = Blueprint('ontology', __name__,
                     template_folder='templates/ontology/')


@ontology.route('/')
def index():
    return 'Hello cliche!'


@ontology.route('/<type_>/')
def list_(type_):
    temp = type_map.get(type_)
    if temp:
        type_name, type_class, type_field = temp
        res = [
            line[0]
            for line in session.query(type_field).order_by(type_field)
        ]
        return render_template(
            'list.html',
            page_title='cliche.io - list of ' + type_name,
            type=type_name,
            list=res
        )
    else:
        abort(404)


@ontology.route('/<type_>/<path:title>/')
def page(type_, title):
    temp = type_map.get(type_)
    if temp:
        type_name, type_class, type_field = temp
        try:
            res = session.query(type_class).filter(type_field == title).one()
        except NoResultFound:
            abort(404)
        return render_template(
            'page_%s.html' % type_,
            page_title='cliche.io - contents of ' + title,
            type=type_name,
            title=title,
            res=res
        )
    else:
        abort(404)
