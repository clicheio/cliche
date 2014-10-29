""":mod:`cliche.services.wikipedia.crawler` --- Wikipedia_ crawler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Crawling DBpedia tables into a relational database

.. seealso::

   `The list of dbpedia classes`__
      This page describes the structure and relation of DBpedia classes.

   __ http://mappings.dbpedia.org/server/ontology/classes/

.. _Wikipedia: http://wikipedia.org/

References
----------
"""
from SPARQLWrapper import JSON, SPARQLWrapper
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import func

from .work import Entity, Relation
from ...celery import app, get_session


PAGE_ITEM_COUNT = 100
CLASSES = [
    'dbpedia-owl:Artist',
    'dbpedia-owl:Book',
    'dbpedia-owl:Cartoon',
    'dbpedia-owl:Film',
    'dbpedia-owl:WrittenWork',
]
PROPERTIES = [
    'dbpedia-owl:writer',
    'dbpedia-owl:author',
    'dbpprop:author',
]


def select_dbpedia(query):
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setReturnFormat(JSON)
    sparql.setQuery(query)
    tuples = sparql.query().convert()['results']['bindings']
    return[{k: v['value'] for k, v in tupl.items()} for tupl in tuples]


def select_property(s, s_name='property', return_json=False):
    """Get properties of a ontology.

    :param str s: Ontology name of subject.
    :return: list of objects which contain properties.
    :rtype: :class:`list`


    For example::

        select_property(s='dbpedia-owl:Writer', json=True)


    .. code-block:: json

       [{
           'property' : 'rdf:type'
           },{
           'property' : 'owl:sameAs'
       }]
    """
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
    """Get count of all works

    :param list p: List of properties
    :rtype: :class:`int`
    """

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


def count_by_class(class_list):
    """Get count of a ontology class

    :param list class_list: List of properties
    :rtype: :class:`int`
    """

    if not class_list:
        raise ValueError('at least one property required')

    classes = ''
    for x in class_list[:-1]:
        classes += '{{ ?subject a {} . }} UNION'.format(class_list[0])

    classes += '{{ ?subject a {} . }}'.format(class_list[-1])

    query = '''PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
    PREFIX dbpprop: <http://dbpedia.org/property/>
    SELECT DISTINCT
        count(?subject)
    WHERE {{
        {classes}
    }}'''.format(classes=classes)
    return int(select_dbpedia(query)[0]['callret-0'])


def select_by_relation(p, revision, s_name='subject', o_name='object', page=1):
    """Find author of something

    Retrieves the list of s_name and o_name, the relation is
    a kind of ontology properties.

    :param list p: List of properties between s_name and o_name.
    :param str s_name: Name of subject. It doesn't affect the results.
    :param str o_name: Name of object. It doesn't affect the results.
    :param page: The offset of query, each page will return 100 entities.
    :type page: :class:`int`
    :return: list of a dict mapping keys to the matching table row fetched.
    :rtype: :class:`list`

    For example::

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
        ?{s_name}_label
        ?{o_name}
        ?{o_name}_label
        ?revision
    WHERE {{
        ?{s_name} ?p ?{o_name} .
        ?{s_name} rdfs:label ?{s_name}_label .
        ?{o_name} rdfs:label ?{o_name}_label .
    FILTER langMatches( lang(?{s_name}_label), "EN" ) .
    FILTER langMatches( lang(?{o_name}_label), "EN" ) .
    FILTER(
        (  {filt}  )
        && STRSTARTS(STR(?{s_name}), "http://dbpedia.org/")) .
        ?{s_name} dbpedia-owl:wikiPageRevisionID ?revision .
        FILTER( ?revision > {revision} )
    }}
    GROUP BY ?{s_name}
    LIMIT {limit}
    OFFSET {offset}'''.format(
        s_name=s_name,
        o_name=o_name,
        filt=filt,
        limit=PAGE_ITEM_COUNT,
        offset=PAGE_ITEM_COUNT * page,
        revision=revision,
    )
    return select_dbpedia(query)


def select_by_class(s, s_name='subject', entities=[], p=[], page=1):
    """List of **s** which as property as **entities**

    :param str s: Ontology name of subject.
    :param str s_name: Name of subject. It doesn't affect the results.
    :param list entities: List of property ontologies.
    :param page: The offset of query, each page will return 100 entities.
    :type page: :class:`int`
    :return: list of a dict mapping keys which have 'entities' as property.
    :rtype: :class:`list`

    For example::

        select_by_class (s_name='author',
        s=['dbpedia-owl:Artist', 'dbpedia-owl:ComicsCreator'],
        entities=['dbpedia-owl:birthDate', 'dbpprop:shortDescription'])


    .. code-block:: json

       [{
           'author': 'http://dbpedia.org/page/J._K._Rowling',
           'name': 'J. K. Rowling',
           'dob' : '1965-07-31',
           'shortDescription' : 'English writer. Author of the Harry ...'
           },{
           'author': ...
       }]
    """
    if not s:
        raise ValueError('at least one class required')

    query = '''PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
        PREFIX dbpprop: <http://dbpedia.org/property/>
        SELECT DISTINCT
            ?{}\n'''.format(s_name)

    group_concat = ''
    s_property_o = ''
    filt = ''
    if 'rdfs:label' in entities:
        filt = 'filter langMatches( lang(?label), "EN" )'

    for entity in entities:
        if ':' in entity:
            col_name = entity.split(':')[1]
            if '/' in entity:
                col_name = entity.split('/')[1]
        else:
            col_name = entity[:3]

        group_concat += ('?{}\n').format(
            col_name
        )
        s_property_o += '?{} {} ?{} .\n'.format(
            s_name, entity, col_name
        )

    query += group_concat
    query += '''WHERE {{
        {{ ?{} a {} . }}\n'''.format(s_name, s[0])
    for x in s[1:]:
        query += '''UNION
        {{ ?{} a {} . }}\n'''.format(s_name, x)
    for prop in p:
        query += '''UNION {{ ?{} ?{} ?prop . }}\n'''.format(s_name, prop)
    query += s_property_o
    query += filt
    query += '''}}
    GROUP BY ?{s_name}
    LIMIT {limit}
    OFFSET {offset}'''.format(
        s_name=s_name,
        limit=PAGE_ITEM_COUNT,
        offset=PAGE_ITEM_COUNT * (page - 1)
    )
    return select_dbpedia(query)


@app.task
def crawl_classes(page, class_num, revision):
    session = get_session()
    res = select_by_class(
        s=CLASSES,
        s_name='work',
        entities=[
            'dbpedia-owl:wikiPageRevisionID',
            'rdfs:label',
            'dbpprop:country',
        ],
        page=page,
        p=PROPERTIES,
    )

    for item in res:
        try:
            with session.begin():
                new_entity = Entity(
                    name=item['work'],
                    revision=item['wikiPageRevisionID'],
                    label=item['label'],
                    country=item['country'],
                )
                session.add(new_entity)
        except IntegrityError:
            pass

    result_len = len(res)
    current_retrieved = (page * PAGE_ITEM_COUNT) + result_len

    if (class_num <= current_retrieved and result_len == PAGE_ITEM_COUNT):
        crawl_classes.delay(
            page + 1,
            current_retrieved + PAGE_ITEM_COUNT,
            revision
        )

    if app.conf['CELERY_ALWAYS_EAGER']:
        return


@app.task
def crawl_relation(page, relation_num, revision):
    session = get_session()
    res = select_by_relation(
        p=[
            'dbpprop:author',
            'dbpedia-owl:writer',
            'dbpedia-owl:author'
        ],
        revision=revision,
        s_name='work',
        o_name='author',
        page=page
    )

    for item in res:
        try:
            with session.begin():
                new_entity = Relation(
                    work=item['work'],
                    work_label=item['work_label'],
                    author=item['author'],
                    author_label=item['author_label'],
                    revision=item['revision'],
                )
                session.add(new_entity)
        except IntegrityError:
            pass
    result_len = len(res)
    current_retrieved = (page * PAGE_ITEM_COUNT) + result_len
    if (relation_num <= current_retrieved and result_len == PAGE_ITEM_COUNT):
        crawl_relation.delay(
            page + 1,
            current_retrieved + PAGE_ITEM_COUNT,
            revision
        )

    if app.conf['CELERY_ALWAYS_EAGER']:
        return


@app.task
def crawl():
    relation_revision = \
        get_session().query(func.max(Relation.revision)).scalar()
    if not relation_revision:
        relation_revision = 0
    relation_num = count_by_relation(
        p=[
            'dbpprop:author',
            'dbpedia-owl:writer',
            'dbpedia-owl:author'
        ]
    )
    for x in range(0, relation_num // PAGE_ITEM_COUNT + 1):
        crawl_relation.delay(x, relation_num, relation_revision)

    class_revision = get_session().query(func.max(Entity.revision)).scalar()
    if not class_revision:
        class_revision = 0
    class_num = count_by_class(
        class_list=CLASSES
    )
    for x in range(0, class_num // PAGE_ITEM_COUNT + 1):
        crawl_classes.delay(x, class_num, class_revision)
