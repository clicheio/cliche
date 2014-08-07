import sqlite3
import urllib.parse

from SPARQLWrapper import SPARQLWrapper, JSON

import pytest

TABLENAME = 'allworkswith'
PRIMARY = 'work'
FOREIGN = 'author'


@pytest.fixture
def fx_table():
    ''' (TABLENAME, PRIMARY, FOREIGN) '''
    ARGS = [
    ]
    for x in range(0, 7):
        ('allworks', 'work', 'author', 40000, x)
    return ARGS


@pytest.fixture
def fx_cursor():
    db_file = '{}.tmp'.format(TABLENAME)
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    return c


def load_dbpedia(tablename, primary, foreign, LIMIT, page):
    ''' used OFFSET and LIMIT(40,000) for paging query '''
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setReturnFormat(JSON)
    query = '''
    PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
    PREFIX dbpprop: <http://dbpedia.org/property/>
    SELECT DISTINCT *
    WHERE {
         ?work ?p ?author
        FILTER(
            ( ?p = dbpprop:author ||
            ?p = dbpedia-owl:author ||
            ?p = dbpedia-owl:writer ) &&
            STRSTARTS(STR(?work), "http://dbpedia.org/"))
    }
    LIMIT 40000
    OFFSET'''
    query += (' ' + str(LIMIT*page))
    print(query)
    sparql.setQuery(query)
    res = sparql.query().convert()
    return res


def test_load_dbpedia(fx_table, fx_cursor):
    for x in fx_table:
        res = load_dbpedia(*x)
        assert fx_cursor.execute(
            'SELECT COUNT({}) FROM {}'
            .format(PRIMARY, TABLENAME)).fetchone()[0] == x[3]*x[4]


# sqlite3
def save_db(tuples, cur):
    start_idx = len('http://dbpedia.org/resource/')
    for result in tuples["results"]["bindings"]:
            PRI = urllib.parse.unquote(result[PRIMARY]["value"])
            FOR = urllib.parse.unquote(result[FOREIGN]["value"])
            cur.execute('INSERT OR IGNORE INTO {} VALUES (?, ?)'
                        .format(TABLENAME),
                        (PRI[start_idx:], FOR[start_idx:]))


@pytest.fixture
def cursor():
    db_file = '{}.tmp'.format(TABLENAME)
    conn = sqlite3.connect(db_file)
    return conn.cursor()


def test_save_db(cursor):
    pass
#    assert cursor.execute(
#        'SELECT COUNT({}) FROM {}'
#        .format(PRIMARY, TABLENAME)).fetchone()[0] == 231512


db_file = '{}.tmp'.format(TABLENAME)
conn = sqlite3.connect(db_file)
c = conn.cursor()

c.execute('''
    CREATE TABLE {} (
        {} text PRIMARY KEY,
        {FOREIGN} text,
        FOREIGN KEY({FOREIGN}) REFERENCES artists(artist)
    )
'''.format(TABLENAME, PRIMARY, FOREIGN=FOREIGN))

LIMIT = 40000
for x in range(0, 7):
    save_db(load_dbpedia(TABLENAME, PRIMARY, FOREIGN, LIMIT, x), c)
conn.commit()
