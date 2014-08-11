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
        SELECT DISTINCT 
            STRAFTER( STR(?work), "http://dbpedia.org/resource/") as ?work
            (group_concat(STRAFTER( STR(?author), "http://dbpedia.org/resource/") ; SEPARATOR=", ") as ?author)
        WHERE {
            ?work ?p ?author
        FILTER(
            ( ?p = dbpprop:author || ?p = dbpedia-owl:author || ?p = dbpedia-owl:writer ) 
            && STRSTARTS(STR(?work), "http://dbpedia.org/")) 
        }
        GROUP BY ?work
        LIMIT
        '''
    query += (' ' + str(LIMIT) + ' OFFSET')
    query += (' ' + str(LIMIT*page))
    print(query)
    sparql.setQuery(query)
    res = sparql.query().convert()
    return res


# sqlite3
def save_db(tuples, table):
    db_file = '{}.tmp'.format(table['TABLENAME'])
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS {} (
            {} text PRIMARY KEY,
            {FOREIGN} text,
            FOREIGN KEY({FOREIGN}) REFERENCES artists(artist)
        )
    '''.format(table['TABLENAME'], table['PRIMARY'], FOREIGN=table['FOREIGN']))
    for result in tuples["results"]["bindings"]:
            PRI = urllib.parse.unquote(result[table['PRIMARY']]["value"])
            FOR = urllib.parse.unquote(result[table['FOREIGN']]["value"])
            print(PRI)
            cur.execute('INSERT OR IGNORE INTO {} VALUES (?, ?)'
                        .format(table['TABLENAME']), (PRI, FOR))
    conn.commit()


if __name__ == "__main__":
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
    conn.commit()
