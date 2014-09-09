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


def select_dbpedia(query):
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setReturnFormat(JSON)
    sparql.setQuery(query)
    tuples = sparql.query().convert()['results']['bindings']
    return[{k: v['value'] for k, v in mydict.items()} for mydict in tuples]


def select_property(s='dbpedia-owl:Writer', s_name='property', json=False):
    prefix = {
        'owl:': 'http://www.w3.org/2002/07/owl#',
        'xsd:': 'http://www.w3.org/2001/XMLSchema#',
        'rdfs:': 'http://www.w3.org/2000/01/rdf-schema#',
        'rdf:': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'foaf:': 'http://xmlns.com/foaf/0.1/',
        'dc:': 'http://purl.org/dc/elements/1.1/',
        ':': 'http://dbpedia.org/resource/',
        'dbpedia2:': 'http://dbpedia.org/property/',
        'dbpedia:': 'http://dbpedia.org/',
        'skos:': 'http://www.w3.org/2004/02/skos/core#',
        'dbpedia-owl:': 'http://dbpedia.org/ontology/',
        'dbpprop:': 'http://dbpedia.org/property/'
        }

    query = '''
    select distinct ?property where{{
        {{
            ?property rdfs:domain ?class .
            {} rdfs:subClassOf+ ?class.
        }} UNION {{
            ?property rdfs:domain {}.
        }}
    }}
    '''.format(s, s)

    p = select_dbpedia(query)

    if json is True:
        return p
    else:
        for x in p:
            for k, v in prefix.items():
                x['property'] = x['property'].replace(v, k)

        pts = [tu['property'] for tu in p]

        return pts


def select_by_relation(
    p=['dbpprop:author', 'dbpedia-owl:writer', 'dbpedia-owl:author'],
        s_name='subject', o_name='object', limit=None):
    if(len(p) < 1):
        raise ValueError('at least one porperty required')

    filt = '?p = {}'.format(p[0])
    for x in p[1:]:
        filt += '\n            || ?p = {}'.format(x)
    query = '''
        PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
        PREFIX dbpprop: <http://dbpedia.org/property/>
        SELECT DISTINCT
            ?{s_name}
            (group_concat( STR(?{o_name}) ; SEPARATOR="\\n") as ?{o_name})
        WHERE {{
            ?{s_name} ?p ?{o_name}
        FILTER(
            (  {filt}  )
            && STRSTARTS(STR(?{s_name}), "http://dbpedia.org/"))
        }}
        GROUP BY ?{s_name}
        LIMIT 30
        OFFSET 30
        '''.format(s_name=s_name, o_name=o_name, filt=filt)
    print(query)
    return select_dbpedia(query)


def select_by_class(s=['dbpedia-owl:Person'],
                    s_name='subject', entity=['foaf:name'], limit=None):
    if(len(s) < 1):
        raise ValueError('at least one class required')

    query = '''
    PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
    PREFIX dbpprop: <http://dbpedia.org/property/>
    SELECT DISTINCT
        ?{}\n'''.format(s_name)

    sel = ''
    cnd = ''

    for x in entity:
        if ':' in x:
            col_name = x.split(':')[1]
            if '/' in x:
                col_name = x.split('/')[1]
        else:
            col_name = x[:3]
        sel += '        (group_concat( STR(?{}) ; SEPARATOR="\\n") as ?{})\n' \
            .format(col_name, col_name)
        cnd += '        ?{} {} ?{} .\n'.format(s_name, x, col_name)

    query += sel
    query += '''    WHERE {{
        {{ ?{} a {} . }}'''.format(s_name, s[0])
    for x in s[1:]:
        query += '''UNION
        {{ ?{} a {} . }}'''.format(s_name, x)
    query += '\n'
    query += cnd
    query += '''        }}
    GROUP BY ?{}
    '''.format(s_name)
    print(query)
    if limit is not None:
        query += 'LIMIT {}'.format(limit)
    return select_dbpedia(query)


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
    pass
    # TABLE = {
    #     'TABLENAME': 'allworks',
    #     'PRIMARY': 'work',
    #     'FOREIGN': 'author',
    #     'LIMIT': 30000,
    #     'COUNT': 8
    # }

    # for x in range(0, TABLE['COUNT']):
    #     save_db(load_dbpedia(TABLE['LIMIT'], x), TABLE)
