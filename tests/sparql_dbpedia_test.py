import json

import pprint

from sparql import load_dbpedia as dbpedia


def test_select_property():
    fp = open('select_artist.json')
    tst = json.load(fp)
    res = dbpedia.select_property(s='dbpedia-owl:Person', json=True)
    assert tst != res
    fp.close()


def test_select_by_relation():
    def mockreturn(f):
        return 'a'
    res = dbpedia.select_by_relation(
        p=[
            'dbpprop:author',
            'dbpedia-owl:writer',
            'dbpedia-owl:author'
        ],
        s_name='work',
        o_name='author',
        limit=10)
    pprint.pprint(res)


def test_select_by_class():
    # fp = open('')
    # tst = json.load(fp)
    res = dbpedia.select_by_class(
        s=['dbpedia-owl:Artist'],
        s_name='artists',
        entity=[
            'foaf:name',
            'dbpedia-owl:birthDate',
            'dbpedia-owl:description'
            ],
        limit=10)
    print(res)
    # fp.close()
