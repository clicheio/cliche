""":mod:`cliche.services.align` --- String matching to align
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import difflib

from urllib.parse import unquote_plus

from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.types import Integer, String

from ..name import Name
from ..orm import Base
from ..sqltypes import HashableLocale as Locale
from ..web.app import app
from ..web.db import session
from ..work import Work
from .tvtropes.entities import ClicheTvtropesEdge, Entity as Tvtropes
from .wikipedia.work import ClicheWikipediaEdge, Entity as Wikipedia


class ExternalId(Base):
    """Relationship between two kinds of external works
    This class can be replaced based on the probability of equality."""

    #: (:class:`int`) The primary key integer.
    id = Column(Integer, primary_key=True)

    #: (:class:`int`) foreignkey for works.id
    work_id = Column(Integer, ForeignKey('works.id'), nullable=False)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`cliche.work.Entity`.
    work = relationship(lambda: Work)

    #: (:class:`str`) The namespace of the trope,
    #: both namespace and name determines one trope.
    tvtropes_namespace = Column(String)

    #: (:class:`str`) The name of the trope.
    tvtropes_name = Column(String)

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`cliche.services.tvtropes.entities.Entity`.
    tvtropes = relationship('cliche.services.tvtropes.entities.Entity')

    #: (:class:`str`) The namespace of the trope.
    wikipedia_id = Column(String, ForeignKey('wikipedia_entities.name'))

    #: (:class:`collections.abc.MutableSet`) The set of
    #: :class:`cliche.services.wikipedia.work.Entity`.
    wikipedia = relationship('cliche.services.wikipedia.work.Entity')

    __tablename__ = 'external_ids'
    __table_args__ = (
        ForeignKeyConstraint(
            [tvtropes_namespace, tvtropes_name],
            [Tvtropes.namespace, Tvtropes.name]
        ),
    )


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
                    work = Work(media_type=wiki[2])
                    work.names.update({
                        Name(nameable=work,
                             name=trope[0],
                             locale=Locale.parse('en_US'))
                    })
                    external_id = ExternalId(
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
                    with session.begin():
                        session.add_all([work, external_id])
            else:
                with app.app_context():
                    wikipedia_work = Work(media_type=wiki[2])
                    wikipedia_work.names.update({
                        Name(nameable=wikipedia_work,
                             name=wiki[0],
                             locale=Locale.parse('en_US'))
                    })
                    wikipedia_edge = ClicheWikipediaEdge(
                        cliche_work=wikipedia_work,
                        wikipedia_name=wiki[1],
                        wikipedia_work=session.query(Wikipedia).
                        filter_by(name=wiki[1]).first()
                    )

                    tvtropes_work = Work(media_type='work')
                    tvtropes_work.names.update({
                        Name(nameable=tvtropes_work,
                             name=trope[0],
                             locale=Locale.parse('en_US'))
                    })
                    tvtropes_edge = ClicheTvtropesEdge(
                        cliche_work=tvtropes_work,
                        tvtropes_namespace=trope[2],
                        tvtropes_name=trope[1],
                        tvtropes_entity=session.query(Tvtropes).
                        filter_by(name=trope[1], namespace=trope[2]).first()
                    )

                    with session.begin():
                        session.add_all([wikipedia_work, tvtropes_work,
                                         wikipedia_edge, tvtropes_edge])

            if trope[0] > wiki[0]:
                wiki = next(wiki_iter)
            else:
                trope = next(tv_iter)
        except StopIteration:
            break


def matching_from_cliche_tvtropes_edges():
    # assume there are a few cliche-tvtropes edges

    with app.app_context():
        with session.begin():
            session.query(ClicheTvtropesEdge).update({'available': True})

            while True:
                max_conf = session \
                    .query(func.max(ClicheTvtropesEdge.confidence)) \
                    .filter_by(available=True) \
                    .scalar()
                if not max_conf:
                    break

                matching = session \
                    .query(ClicheTvtropesEdge) \
                    .filter_by(confidence=max_conf, available=True) \
                    .first()

                cliche_work = matching.cliche_work
                tvtropes_entity = matching.tvtropes_entity

                session.query(ClicheTvtropesEdge) \
                       .filter_by(cliche_work=cliche_work,
                                  available=True) \
                       .update({'available': False})

                session.query(ClicheTvtropesEdge) \
                       .filter_by(tvtropes_entity=tvtropes_entity,
                                  available=True) \
                       .update({'available': False})

                yield matching


def matching_from_cliche_wikipedia_edges():
    # assume there are a few cliche-wikipedia edges

    with app.app_context():
        with session.begin():
            session.query(ClicheWikipediaEdge).update({'available': True})

            while True:
                max_conf = session \
                    .query(func.max(ClicheWikipediaEdge.confidence)) \
                    .filter_by(available=True) \
                    .scalar()
                if not max_conf:
                    break

                matching = session \
                    .query(ClicheWikipediaEdge) \
                    .filter_by(confidence=max_conf, available=True) \
                    .first()

                cliche_work = matching.cliche_work
                wikipedia_work = matching.wikipedia_work

                session.query(ClicheWikipediaEdge) \
                       .filter_by(cliche_work=cliche_work,
                                  available=True) \
                       .update({'available': False})

                session.query(ClicheWikipediaEdge) \
                       .filter_by(wikipedia_work=wikipedia_work,
                                  available=True) \
                       .update({'available': False})

                yield matching
