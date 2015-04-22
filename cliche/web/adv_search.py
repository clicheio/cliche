from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy.orm.exc import NoResultFound

from ..sqltypes import HashableLocale as Locale
from ..work import Trope, Work
from .db import session


adv_search_bp = Blueprint('adv_search', __name__)


@adv_search_bp.route('/', methods=['POST'])
def result():
    about = request.form.getlist('about[]', None)
    category = request.form.getlist('category[]', None)
    detail = request.form.getlist('detail[]', None)
    error_redirect = redirect(url_for('index'))

    if about is None or category is None or detail is None:
        flash('Invalid arguments.', 'danger')
        return error_redirect

    if type(about) != list or type(category) != list or type(detail) != list:
        flash('Invalid arguments..', 'danger')
        return error_redirect

    if len(about) != len(category) or len(about) != len(detail):
        flash('Invalid arguments...', 'danger')
        return error_redirect

    query = zip(about, category, detail)

    media_list = []
    trope_filter = None
    for about, category, detail in query:
        if about == 'info':
            if category == 'media':
                media_list.append(detail)
        elif about == 'trope':
            try:
                trope = session.query(Trope).get(detail)
            except NoResultFound:
                return error_redirect

            if trope_filter is None:
                trope_filter = Work.tropes.any(Trope.id == trope.id)
            else:
                trope_filter = trope_filter & \
                    Work.tropes.any(Trope.id == trope.id)

    if not media_list and trope_filter is None:
        flash('Invalid arguments....', 'danger')
        return error_redirect

    result = session.query(
        Work,
        Work.canonical_name(Locale.parse('en_US')).label('canonical_name')
    )

    if media_list:
        result = result.filter(Work.media_type.in_(media_list))

    if trope_filter is not None:
        result = result.filter(trope_filter)

    return render_template('adv_search/result.html', result=result)
