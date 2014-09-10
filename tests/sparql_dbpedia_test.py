import json

from sparql import load_dbpedia as dbpedia


def test_select_property(monkeypatch):
    class fakeQuery(object):
        def convert(self):
            with open('tests/select_property.json') as fp:
                fakeResult = (json.load(fp))
                return {"results": {"bindings": fakeResult}}

    monkeypatch.setattr("SPARQLWrapper.SPARQLWrapper.query", fakeQuery)
    res = dbpedia.select_property(s='dbpedia-owl:Person', json=True)
    assert type(res[0]['property']) == str


def test_select_by_relation(monkeypatch):
    class fakeQuery(object):
        offset = 0

        def convert(self):
            with open('tests/select_relation.json') as fp:
                offset = fakeQuery.offset
                fakeResult = (json.load(fp))[offset:offset+100:]
                fakeQuery.offset += 100
                return {"results": {"bindings": fakeResult}}

    monkeypatch.setattr("SPARQLWrapper.SPARQLWrapper.query", fakeQuery)

    res = dbpedia.select_by_relation(
        p=[
            'dbpprop:author',
            'dbpedia-owl:writer',
            'dbpedia-owl:author'
        ],
        s_name='work',
        o_name='author',
        limit=101)
    assert len(res) == 101


def test_select_by_class(monkeypatch):
    class fakeQuery(object):
        offset = 0

        def convert(self):
            with open('tests/select_class.json') as fp:
                offset = fakeQuery.offset
                fakeResult = (json.load(fp))[offset:offset+100:]
                fakeQuery.offset += 100
                return {"results": {"bindings": fakeResult}}

    monkeypatch.setattr("SPARQLWrapper.SPARQLWrapper.query", fakeQuery)

    res = dbpedia.select_by_class(
        s=['dbpedia-owl:Artist'],
        s_name='artists',
        entity=['foaf:name', 'dbpedia-owl:birthDate'],
        limit=3)
    assert len(res) == 3
