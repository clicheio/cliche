import json

from sparql import load_dbpedia as dbpedia


def test_select_property():
    fp = open('select_artist.json')
    fakeResult = json.load(fp)
    res = dbpedia.select_property(s='dbpedia-owl:Person', json=True)
    assert fakeResult != res
    fp.close()


def test_select_by_relation(monkeypatch):
    class fakeQuery(object):
        offset = 0

        def convert(self):
            fp = open('select_relation.json')
            offset = fakeQuery.offset
            fakeResult = (json.load(fp))[offset:offset+100:]
            fakeQuery.offset += 100
            fp.close()
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
            fp = open('select_class.json')
            offset = fakeQuery.offset
            fakeResult = (json.load(fp))[offset:offset+100:]
            fakeQuery.offset += 100
            fp.close()
            return {"results": {"bindings": fakeResult}}

    monkeypatch.setattr("SPARQLWrapper.SPARQLWrapper.query", fakeQuery)

    res = dbpedia.select_by_class(
        s=['dbpedia-owl:Artist'],
        s_name='artists',
        entity=[
            'foaf:name',
            'dbpedia-owl:birthDate'
            ],
        limit=3)
    assert len(res) == 3
