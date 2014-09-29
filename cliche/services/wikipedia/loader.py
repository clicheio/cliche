""":mod:`cliche.services.wikipedia.loader` --- Wikipedia_ loader
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Loading DBpedia tables into a relational database

.. seealso::

   `The list of dbpedia classes`__
      This page describes the structure and relation of DBpedia classes.

   __ http://mappings.dbpedia.org/server/ontology/classes/

.. _Wikipedia: http://wikipedia.org/

References
----------
"""
from celery.utils.log import get_task_logger
from sqlalchemy.exc import IntegrityError
from SPARQLWrapper import JSON, SPARQLWrapper

from .workauthor import WorkAuthor
from ...celery import app, get_session


PAGE_ITEM_COUNT = 100


def select_dbpedia(query):
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setReturnFormat(JSON)
    sparql.setQuery(query)
    tuples = sparql.query().convert()['results']['bindings']
    return[{k: v['value'] for k, v in tupl.items()} for tupl in tuples]


def select_property(s, s_name='property', return_json=False):
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

    if return_json:
        return properties
    else:
        for property_ in properties:
            for k, v in prefix.items():
                property_['property'] = property_['property'].replace(v, k)
        tuples = [tupl['property'] for tupl in properties]
        return tuples


def count_by_relation(p):
    """Get count of all works"""

    if not p:
        raise ValueError('at least one property required')

    filt = '?p = {}'.format(p[0])
    for x in p[1:]:
        filt += '\n            || ?p = {}'.format(x)

    query = '''PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
    PREFIX dbpprop: <http://dbpedia.org/property/>
    SELECT DISTINCT
        count(?work)
    WHERE {{
        ?work ?p ?author
    FILTER(
        (  {filt}  )
        && STRSTARTS(STR(?work), "http://dbpedia.org/"))
    }}
    '''.format(filt=filt)

    return int(select_dbpedia(query)[0]['callret-0'])


def select_by_relation(p, s_name='subject', o_name='object', page=1):
    """Find author of somethings

    Retrieves the list of s_name and o_name, the relation is
    a kind of ontology properties.

    :param list p: List of properties between s_name and o_name.
    :param str s_name: Name of subject. It doesn't affect to the results.
    :param str o_name: Name of object. It doesn't affect to the results.
    :param page: The offset of query, each page will return 100 entities.
    :type page: integer
    :return: list of a dict mapping keys to the corresponding table row fetched.
    :rtype: :class:`list`

    For example:

    .. code-block:: console

        select_by_relation(s_name='work',
        p=['dbpprop:author', 'dbpedia-owl:writer', 'dbpedia-owl:author'],
        o_name='author', page=0)


    .. code-block:: json

        [{
            'work':'http://dbpedia.org/resource/The_Frozen_Child',
            'author': 'http://dbpedia.org/resource/József_Eötvös
            http://dbpedia.org/resource/Ede_Sas'
            },{
            'work':'http://dbpedia.org/resource/Slaves_of_Sleep',
            'author': 'http://dbpedia.org/resource/L._Ron_Hubbard'
        }]

    When the row has more than two items, the items are combined by EOL.
    """
    if not p:
        raise ValueError('at least one property required')

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
        GROUP BY ?{s_name}
        LIMIT {limit}
        OFFSET {offset}'''.format(
            s_name=s_name,
            o_name=o_name,
            filt=filt,
            limit=PAGE_ITEM_COUNT,
            offset=PAGE_ITEM_COUNT * page
        )
    return select_dbpedia(query)


def select_by_class(s, s_name='subject', entities=None, page=1):
    """List of Artist and ComicsCreator"""
    if not s:
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

        group_concat += ('(group_concat( STR(?{}) ; '
                         'SEPARATOR="\\n") as ?{})\n').format(
            col_name, col_name
        )
        s_property_o += '        ?{} {} ?{} .\n'.format(
            s_name, entity, col_name
        )

    query += group_concat
    query += '''    WHERE {{
        {{ ?{} a {} . }}'''.format(s_name, s[0])
    for x in s[1:]:
        query += '''UNION
        {{ ?{} a {} . }}\n'''.format(s_name, x)
    query += s_property_o
    query += '''        }}
    GROUP BY ?{s_name}
    LIMIT {limit}
    OFFSET {offset}'''.format(
        s_name=s_name,
        limit=PAGE_ITEM_COUNT,
        offset=PAGE_ITEM_COUNT * (page-1)
    )
    return select_dbpedia(query)


@app.task
def load_page(page, relation_num):
    session = get_session()
    res = select_by_relation(
        p=[
            'dbpprop:author',
            'dbpedia-owl:writer',
            'dbpedia-owl:author'
        ],
        s_name='work',
        o_name='author',
        page=page
    )

    for item in res:
        try:
            with session.begin():
                new_entity = WorkAuthor(
                    work=item['work'],
                    author=item['author'],
                )
                session.add(new_entity)
        except IntegrityError:
            pass

    logger = get_task_logger(__name__ + '.load_page')
    result_len = len(res)
    current_retrieved = (page * PAGE_ITEM_COUNT) + result_len
    logger.warning('loaded %d/%d', current_retrieved, relation_num)
    if (relation_num <= current_retrieved and result_len == PAGE_ITEM_COUNT):
        load_page.delay(page + 1, current_retrieved + PAGE_ITEM_COUNT)

    if app.conf['CELERY_ALWAYS_EAGER']:
        return


@app.task
def load():
    relation_num = count_by_relation(
        p=[
            'dbpprop:author',
            'dbpedia-owl:writer',
            'dbpedia-owl:author'
        ]
    )
    for x in range(0, relation_num//PAGE_ITEM_COUNT + 1):
        load_page.delay(x, relation_num)
