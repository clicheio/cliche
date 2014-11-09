import json
import os.path

from cliche.services.wikipedia import crawler as dbpedia


def test_select_property(monkeypatch):
    class FakeQuery(object):
        def convert(self):
            with open(os.path.join(os.path.dirname(__file__),
                      'select_property.json')) as fp:
                fakeResult = (json.load(fp))
                return {"results": {"bindings": fakeResult}}

    monkeypatch.setattr("SPARQLWrapper.SPARQLWrapper.query", FakeQuery)
    res = dbpedia.select_property(s='dbpedia-owl:Person', return_json=True)
    assert type(res[0]['property']) == str


def test_count_by_relation(monkeypatch):
    class FakeQuery(object):
        def convert(self):
            return {
                "results": {
                    "bindings": [
                        {"callret-0": {"value": "251083"}}
                    ]
                }
            }

    monkeypatch.setattr("SPARQLWrapper.SPARQLWrapper.query", FakeQuery)
    res = dbpedia.count_by_relation(
        p=[
            'dbpprop:author',
            'dbpedia-owl:writer',
            'dbpedia-owl:author'
        ]
    )
    assert res > 250000


def test_count_by_classes(monkeypatch):
    class FakeQuery(object):
        def convert(self):
            return {
                "results": {
                    "bindings": [
                        {"callret-0": {"value": "826905"}}
                    ]
                }
            }

    monkeypatch.setattr("SPARQLWrapper.SPARQLWrapper.query", FakeQuery)
    res = dbpedia.count_by_class(
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
    assert res > 820000


def test_select_by_relation(monkeypatch):
    class FakeQuery(object):
        offset = 0

        def convert(self):
            with open(os.path.join(os.path.dirname(__file__),
                      'select_relation.json')) as fp:
                offset = FakeQuery.offset
                fakeResult = (json.load(fp))[offset:offset+100:]
                FakeQuery.offset += 100
                return {"results": {"bindings": fakeResult}}

    monkeypatch.setattr("SPARQLWrapper.SPARQLWrapper.query", FakeQuery)

    res = dbpedia.select_by_relation(
        p=[
            'dbpprop:author',
            'dbpedia-owl:writer',
            'dbpedia-owl:author'
        ],
        revision=0,
        s_name='work',
        o_name='author',
        page=1
    )
    assert len(res) == 100


def test_select_by_class(monkeypatch):
    class FakeQuery(object):
        offset = 0

        def convert(self):
            with open(os.path.join(os.path.dirname(__file__),
                      'select_class.json')) as fp:
                offset = FakeQuery.offset
                fakeResult = json.load(fp)[offset:offset+100:]
                FakeQuery.offset += 100
                return {"results": {"bindings": fakeResult}}

    monkeypatch.setattr("SPARQLWrapper.SPARQLWrapper.query", FakeQuery)

    res = dbpedia.select_by_class(
        s=['dbpedia-owl:Artist'],
        s_name='artists',
        entities=['foaf:name', 'dbpedia-owl:birthDate'],
        page=1
    )
    assert len(res) == 100
