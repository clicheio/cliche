import sqlite3
import urllib.parse

from SPARQLWrapper import SPARQLWrapper, JSON

import pytest


def load_dbpedia(LIMIT, page):
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
    # print(query)
    sparql.setQuery(query)
    res = sparql.query().convert()
    return res


# sqlite3
def save_db(tuples, cur, table):
    start_idx = len('http://dbpedia.org/resource/')
    for result in tuples["results"]["bindings"]:
            PRI = urllib.parse.unquote(result[table['PRIMARY']]["value"])
            FOR = urllib.parse.unquote(result[table['FOREIGN']]["value"])
            cur.execute('INSERT OR IGNORE INTO {} VALUES (?, ?)'
                        .format(table['TABLENAME']),
                        (PRI[start_idx:], FOR[start_idx:]))


TABLE = {
    'TABLENAME': 'allworks',
    'PRIMARY': 'work',
    'FOREIGN': 'author',
    'LIMIT': 40000,
    'COUNT': 7
}

db_file = '{}.tmp'.format(TABLE['TABLENAME'])
conn = sqlite3.connect(db_file)
c = conn.cursor()

c.execute('''
    CREATE TABLE {} (
        {} text PRIMARY KEY,
        {FOREIGN} text,
        FOREIGN KEY({FOREIGN}) REFERENCES artists(artist)
    )
'''.format(TABLE['TABLENAME'], TABLE['PRIMARY'], FOREIGN=TABLE['FOREIGN']))

for x in range(0, 7):
    save_db(load_dbpedia(TABLE['LIMIT'], x), c, TABLE)
conn.commit()
