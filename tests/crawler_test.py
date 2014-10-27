import json

from sqlalchemy.sql.expression import func

from cliche.services.wikipedia import crawler as dbpedia
from cliche.services.wikipedia.work import Entity, Relation


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


def test_class_crawler(monkeypatch, fx_session, fx_celery_app):
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

    class_num = dbpedia.count_by_class(
        class_list=[
            'dbpedia-owl:Artist',
            'dbpedia-owl:Artwork',
            'dbpedia-owl:Book',
            'dbpedia-owl:Comic',
            'dbpedia-owl:Comics',
            'dbpedia-owl:ComicsCreator',
            'dbpedia-owl:Drama',
            'dbpedia-owl:Writer',
            'dbpedia-owl:WrittenWork',
        ]
    )
    assert class_num > 0

    class FakeQuery(object):
        offset = 0

        def convert(self):
            with open('tests/select_class_with_revision.json') as fp:
                offset = FakeQuery.offset
                fakeResult = (json.load(fp))[offset:offset+100:]
                FakeQuery.offset += 100
                return {"results": {"bindings": fakeResult}}

    monkeypatch.setattr("SPARQLWrapper.SPARQLWrapper.query", FakeQuery)
    dbpedia.crawl_classes(1, class_num, 0)
    num = fx_session.query(Entity).count()
    assert fx_session.query(func.max(Entity.revision)).scalar() > 0
    assert num == 100
