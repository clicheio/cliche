import json

from sqlalchemy.sql.expression import func

from cliche.services.wikipedia import crawler as dbpedia
from cliche.services.wikipedia.work import (
    Artist, Book, Entity, Film, Relation, Work
)


def test_revision_crawler(monkeypatch, fx_session, fx_celery_app):
    class FakeQuery(object):
        def convert(self):
            return {
                "results": {
                    "bindings": [
                        {"callret-0": {"value": "250280"}}
                    ]
                }
            }

    monkeypatch.setattr("SPARQLWrapper.SPARQLWrapper.query", FakeQuery)

    relation_num = dbpedia.count_by_relation(
        p=[
            'dbpprop:author',
            'dbpedia-owl:writer',
            'dbpedia-owl:author'
        ]
    )
    assert relation_num > 0

    class FakeQuery(object):
        offset = 0

        def convert(self):
            with open('tests/select_relation.json') as fp:
                offset = FakeQuery.offset
                fakeResult = (json.load(fp))[offset:offset+100:]
                FakeQuery.offset += 100
                return {"results": {"bindings": fakeResult}}

    monkeypatch.setattr("SPARQLWrapper.SPARQLWrapper.query", FakeQuery)
    dbpedia.crawl_relation(1, relation_num, 0)
    num = fx_session.query(Relation).count()
    assert fx_session.query(func.max(Relation.revision)).scalar() > 0
    assert num == 100


def test_fetch_Entity(monkeypatch, fx_session, fx_celery_app):

    class FakeQuery(object):
        offset = 0

        def convert(self):
            with open('tests/select_class_with_revision.json') as fp:
                offset = FakeQuery.offset
                fakeResult = (json.load(fp))[offset:offset+100:]
                FakeQuery.offset += 100
                return {"results": {"bindings": fakeResult}}

    monkeypatch.setattr("SPARQLWrapper.SPARQLWrapper.query", FakeQuery)

    dbpedia.fetch_classes(1, Entity, [
        'dbpedia-owl:Cartoon',
        'dbpedia-owl:MovieDirector',
        'dbpedia-owl:Producer',
        'dbpedia-owl:TheatreDirector',
        'dbpedia-owl:TelevisionDirector',
        'dbpedia-owl:TelevisionPersonality'
    ])

    assert fx_session.query(Entity).count() > 0


def test_fetch_Artist(monkeypatch, fx_session, fx_celery_app):

    class FakeQuery(object):
        offset = 0

        def convert(self):
            with open('tests/fetch_artist.json') as fp:
                offset = FakeQuery.offset
                fakeResult = (json.load(fp))[offset:offset+100:]
                FakeQuery.offset += 100
                return {"results": {"bindings": fakeResult}}

    monkeypatch.setattr("SPARQLWrapper.SPARQLWrapper.query", FakeQuery)

    dbpedia.fetch_classes(1, Artist, ['dbpedia-owl:Artist'])
    assert fx_session.query(Artist).count() > 0


def test_fetch_Work(monkeypatch, fx_session, fx_celery_app):

    class FakeQuery(object):
        offset = 0

        def convert(self):
            with open('tests/fetch_work.json') as fp:
                offset = FakeQuery.offset
                fakeResult = (json.load(fp))[offset:offset+100:]
                FakeQuery.offset += 100
                return {"results": {"bindings": fakeResult}}

    monkeypatch.setattr("SPARQLWrapper.SPARQLWrapper.query", FakeQuery)

    dbpedia.fetch_classes(1, Work, ['dbpedia-owl:Work'])
    assert fx_session.query(Work).count() > 0


def test_fetch_Film(monkeypatch, fx_session, fx_celery_app):

    class FakeQuery(object):
        offset = 0

        def convert(self):
            with open('tests/fetch_film.json') as fp:
                offset = FakeQuery.offset
                fakeResult = (json.load(fp))[offset:offset+100:]
                FakeQuery.offset += 100
                return {"results": {"bindings": fakeResult}}

    monkeypatch.setattr("SPARQLWrapper.SPARQLWrapper.query", FakeQuery)

    dbpedia.fetch_classes(1, Film, ['dbpedia-owl:Film'])
    assert fx_session.query(Film).count() > 0


def test_fetch_Book(monkeypatch, fx_session, fx_celery_app):

    class FakeQuery(object):
        offset = 0

        def convert(self):
            with open('tests/fetch_book.json') as fp:
                offset = FakeQuery.offset
                fakeResult = (json.load(fp))[offset:offset+100:]
                FakeQuery.offset += 100
                return {"results": {"bindings": fakeResult}}

    monkeypatch.setattr("SPARQLWrapper.SPARQLWrapper.query", FakeQuery)

    dbpedia.fetch_classes(1, Book, ['dbpedia-owl:Book', 'dbpedia-owl:Novel'])
    assert fx_session.query(Book).count() > 0
