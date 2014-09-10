from SPARQLWrapper import JSON, SPARQLWrapper


def select_dbpedia(query):
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setReturnFormat(JSON)
    sparql.setQuery(query)
    tuples = sparql.query().convert()['results']['bindings']
    return[{k: v['value'] for k, v in tupl.items()} for tupl in tuples]


def select_property(s, s_name='property', json=False):
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

    query = '''select distinct ?property where{{
        {{
            ?property rdfs:domain ?class .
            {} rdfs:subClassOf+ ?class.
        }} UNION {{
            ?property rdfs:domain {}.
        }}
    }}'''.format(s, s)

    properties = select_dbpedia(query)

    if json:
        return properties
    else:
        for p in properties:
            for k, v in prefix.items():
                p['property'] = p['property'].replace(v, k)
        tuples = [tupl['property'] for tupl in properties]
        return tuples


def select_by_relation(p, s_name='subject', o_name='object', limit=None):
    if(len(p) < 1):
        raise ValueError('at least one porperty required')

    filt = '?p = {}'.format(p[0])
    for x in p[1:]:
        filt += '\n            || ?p = {}'.format(x)
    query = '''PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
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
        GROUP BY ?{s_name}'''.format(s_name=s_name, o_name=o_name, filt=filt)
    return paging_query(query, limit)


def select_by_class(s, s_name='subject', entities=None, limit=None):
    if(len(s) < 1):
        raise ValueError('at least one class required')
    if entities is None:
        entities = []

    query = '''PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
        PREFIX dbpprop: <http://dbpedia.org/property/>
        SELECT DISTINCT
            ?{}\n'''.format(s_name)

    group_concat = ''
    s_property_o = ''

    for entity in entities:
        if ':' in entity:
            col_name = entity.split(':')[1]
            if '/' in entity:
                col_name = entity.split('/')[1]
        else:
            col_name = entity[:3]

        group_concat += '        (group_concat( STR(?{}) ; SEPARATOR="\\n") as ?{})\n' \
            .format(col_name, col_name)
        s_property_o += '        ?{} {} ?{} .\n' \
            .format(s_name, entity, col_name)

    query += group_concat
    query += '''    WHERE {{
        {{ ?{} a {} . }}'''.format(s_name, s[0])
    for x in s[1:]:
        query += '''UNION
        {{ ?{} a {} . }}\n'''.format(s_name, x)
    query += s_property_o
    query += '''        }}
    GROUP BY ?{}'''.format(s_name)

    return paging_query(query, limit)


def paging_query(query, limit):
    query_results = []
    if limit is not None:
        query += 'LIMIT {}\n'.format(limit)
        for x in range(0, (limit+99)//100):
            oquery = query + 'OFFSET {}\n'.format(x*100)
            query_results += select_dbpedia(oquery)
        return query_results
    else:
        return select_dbpedia(query)
