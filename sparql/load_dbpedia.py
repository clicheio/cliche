import sqlite3
import urllib.parse

from SPARQLWrapper import JSON, SPARQLWrapper


def load_dbpedia(limit, page):
    ''' used OFFSET and LIMIT(40,000) for paging query '''
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setReturnFormat(JSON)
    query = '''
        PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
        PREFIX dbpprop: <http://dbpedia.org/property/>
        SELECT DISTINCT
            ?work
            (group_concat( STR(?author) ; SEPARATOR="\\n") as ?author)
        WHERE {{
            ?work ?p ?author
        FILTER(
            (      ?p = dbpprop:author
                || ?p = dbpedia-owl:author
                || ?p = dbpedia-owl:writer )
            && STRSTARTS(STR(?work), "http://dbpedia.org/"))
        }}
        GROUP BY ?work
        LIMIT {}
        OFFSET {}
        '''.format(str(limit), str(limit*page))
    sparql.setQuery(query)
    tuples = sparql.query().convert()['results']['bindings']
    return tuples


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
    for result in tuples:
            primary = urllib.parse.unquote(result[table['PRIMARY']]['value'])
            foreign = urllib.parse.unquote(result[table['FOREIGN']]['value'])
            cur.execute('INSERT OR IGNORE INTO {} VALUES (?, ?)'
                        .format(table['TABLENAME']), (primary, foreign))
    conn.commit()


if __name__ == "__main__":
    TABLE = {
        'TABLENAME': 'allworks',
        'PRIMARY': 'work',
        'FOREIGN': 'author',
        'LIMIT': 30000,
        'COUNT': 8
    }

    for x in range(0, TABLE['COUNT']):
        save_db(load_dbpedia(TABLE['LIMIT'], x), TABLE)
