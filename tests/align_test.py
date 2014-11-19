import datetime

from cliche.name import Name
from cliche.services.align import (
    matching_from_cliche_tvtropes_edges, matching_from_cliche_wikipedia_edges
)
from cliche.services.tvtropes.entities import (
    ClicheTvtropesEdge, Entity as TvEntity
)
from cliche.services.wikipedia.work import (
    ClicheWikipediaEdge, Work as WikiWork
)
from cliche.sqltypes import HashableLocale as Locale
from cliche.work import Work


def edge_examples(edges, make_edge):
    edges.append(make_edge(0, 0, 0.55))
    edges.append(make_edge(0, 1, 0.80))
    edges.append(make_edge(0, 2, 0.50))

    edges.append(make_edge(1, 0, 0.95))
    edges.append(make_edge(1, 1, 0.70))
    edges.append(make_edge(1, 2, 0.85))

    edges.append(make_edge(2, 0, 0.65))
    edges.append(make_edge(2, 1, 0.60))
    edges.append(make_edge(2, 2, 1.00))


def example_matching_confidences():
    return {1.00, 0.95, 0.80}


def test_align_from_cliche_tvtrope_edges(fx_session):
    current_time = datetime.datetime.now(datetime.timezone.utc)

    tvtropes_entities = []
    for i in range(1, 4):
        tvtropes_entities.append(
            TvEntity(
                namespace='Main',
                name='Entity_{}'.format(i),
                url='http://tvtropes.org/Main/Entity_{}'.format(i),
                type='Work',
                last_crawled=current_time
            )
        )

    cliche_works = []
    for i in range(1, 4):
        w = Work(media_type='Work')
        w.names.update({
            Name(nameable=w,
                 name='Work_{}'.format(i),
                 locale=Locale.parse('en_US'))
        })
        cliche_works.append(w)

    def make_edge(tvtropes_index, cliche_index, confidence):
        t = tvtropes_entities[tvtropes_index]
        c = cliche_works[cliche_index]
        e = ClicheTvtropesEdge(confidence=confidence)
        e.tvtropes_entity = t
        e.cliche_work = c
        return e

    edges = []
    edge_examples(edges, make_edge)

    with fx_session.begin():
        fx_session.add_all(tvtropes_entities + cliche_works + edges)

    confidences = {
        m.confidence for m in matching_from_cliche_tvtropes_edges()
    }
    assert confidences == example_matching_confidences()


def test_align_from_cliche_wikipedia_edges(fx_session):
    current_time = datetime.datetime.now(datetime.timezone.utc)

    wikipedia_works = []
    for i in range(1, 4):
        wikipedia_works.append(
            WikiWork(name='Entity_{}'.format(i), label='Entity_{}'.format(i),
                     last_crawled=current_time)
        )

    cliche_works = []
    for i in range(1, 4):
        w = Work(media_type='Work')
        w.names.update({
            Name(nameable=w,
                 name='Work_{}'.format(i),
                 locale=Locale.parse('en_US'))
        })
        cliche_works.append(w)

    def make_edge(wikipedia_index, cliche_index, confidence):
        w = wikipedia_works[wikipedia_index]
        c = cliche_works[cliche_index]
        e = ClicheWikipediaEdge(confidence=confidence)
        e.wikipedia_work = w
        e.cliche_work = c
        return e

    edges = []
    edge_examples(edges, make_edge)

    with fx_session.begin():
        fx_session.add_all(wikipedia_works + cliche_works + edges)

    confidences = {
        m.confidence for m in matching_from_cliche_wikipedia_edges()
    }
    assert confidences == example_matching_confidences()


def test_external_ids_of_work(fx_external_ids):
    assert fx_external_ids.jane_eyre_ex
    assert fx_external_ids.jane_eyre_ex.wikipedia_id == \
        'http://dbpedia.org/resource/Jane_Eyre'
