import difflib

from urllib.parse import unquote_plus

from .tvtropes.entities import Entity as Tvtropes
from .wikipedia.work import Entity as Wikipedia
from ..name import Name
from ..sqltypes import HashableLocale as Locale
from ..web.app import app
from ..web.db import session
from ..work import ExternelId, Work


def normalize(name):
    return name.strip().lower()


def url_to_label(url):
    if url:
        label = unquote_plus(url[28:].replace('_', ' ')).strip().lower()
        return label.split('(')[0]
    else:
        return None


def is_same(a_, b_):
    diff = difflib.SequenceMatcher(None, a_, b_).ratio()
    if diff > 0.9:
        return True
    else:
        return False


def alignment():
    with app.app_context():
        tvtropes_list = session \
            .query(Tvtropes.name, Tvtropes.namespace) \
            .order_by(Tvtropes.name).all()
        wikipedia_list = session \
            .query(Wikipedia.name, Wikipedia.label, Wikipedia.type) \
            .order_by(Wikipedia.name).all()

    wikipedia_list = [(url_to_label(x[0]), x[0], x[2]) for x in wikipedia_list]
    tvtropes_list = [(normalize(x[0]), x[0], x[1]) for x in tvtropes_list]
    wikipedia_list.sort()
    tvtropes_list.sort()
    tv_iter = iter(tvtropes_list)
    wiki_iter = iter(wikipedia_list)
    trope = next(tv_iter)
    wiki = next(wiki_iter)
    while(True):
        try:
            if is_same(trope[0], wiki[0]):
                print(trope[0], wiki[0])

                with app.app_context():
                    work = Work()
                    work.names.update({
                        Name(nameable=work,
                             name=trope[0],
                             locale=Locale.parse('en_US'))
                    })
                    externel_id = ExternelId(
                        work_id=work.id,
                        work=work,
                        wikipedia_id=wiki[1],
                        wikipedia=session
                                    .query(Wikipedia)
                                    .filter(Wikipedia.name.like(wiki[1]))
                                    .first(),
                        tvtropes_name=trope[1],
                        tvtropes_namespace=trope[2],
                        tvtropes=session
                                    .query(Tvtropes)
                                    .filter(
                                        Tvtropes.name.like(trope[1]),
                                        Tvtropes.namespace.like(trope[2]))
                                    .first()
                    )
                    work.external_ids.update({externel_id})
                    with session.begin():
                        session.add(work)
                        session.add(externel_id)
            else:
                with app.app_context():
                    wikipedia_work = Work()
                    wikipedia_work.names.update({
                        Name(nameable=wikipedia_work,
                             name=wiki[0],
                             locale=Locale.parse('en_US'))
                    })
                    tvtropes_work = Work()
                    tvtropes_work.names.update({
                        Name(nameable=tvtropes_work,
                             name=trope[0],
                             locale=Locale.parse('en_US'))
                    })
                    with session.begin():
                        session.add(wikipedia_work)
                        session.add(tvtropes_work)

            if trope[0] > wiki[0]:
                wiki = next(wiki_iter)
            else:
                trope = next(tv_iter)
        except StopIteration:
            break
