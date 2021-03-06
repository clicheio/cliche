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
import datetime
from http.client import IncompleteRead
from urllib.error import HTTPError, URLError

from celery.utils.log import get_task_logger
from SPARQLWrapper import JSON, SPARQLWrapper
from SPARQLWrapper.SPARQLExceptions import EndPointNotFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import func

from ...celery import app, get_session
from .work import (
    Artist, Book, Entity, Film, Relation, Work
)


PAGE_ITEM_COUNT = 100


def get_wikipedia_limit():
    return app.conf.get('WIKIPEDIA_RETRY_LIMIT', 20)


def select_dbpedia(query):
    logger = get_task_logger(__name__ + '.select_dbpedia')
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setReturnFormat(JSON)
    sparql.setQuery('''PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
    PREFIX dbpprop: <http://dbpedia.org/property/>'''+query)
    tried = 0
    wikipedia_limit = get_wikipedia_limit()
    while tried < wikipedia_limit:
        try:
            tried = tried + 1
            tuples = sparql.query().convert()['results']['bindings']
        except HTTPError as e:
            logger.exception('HTTPError %s: %s, tried %d/%d',
                             e.code, e.reason, tried, wikipedia_limit)
        except URLError as e:
            logger.exception('URLError %s, tried %d/%d',
                             e.args, tried, wikipedia_limit)
        except ConnectionResetError as e:
            logger.exception('ConnectionResetError %s', e)
        except IncompleteRead as e:
            logger.exception('Network Error, retry %d', tried)
        except EndPointNotFound as e:
            logger.exception('SQLAlchemy Error, retry %d', tried)
        else:
            return[{k: v['value'] for k, v in tupl.items()} for tupl in tuples]
    return []


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

    query = '''SELECT DISTINCT ?property WHERE{{
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

    query = '''SELECT DISTINCT
        count(?work)
    WHERE {{
        ?work ?p ?author
    FILTER(
        (  {filt}  )
        && STRSTARTS(STR(?work), "http://dbpedia.org/"))
    }}
    '''.format(filt=' || '.join('?p = %s\n' % x for x in p))

    cnt = select_dbpedia(query)
    if cnt:
        return int(cnt[0]['callret-0'])
    else:
        return 0


def count_by_class(class_list):
    """Get count of a ontology class

    :param list class_list: List of properties
    :rtype: :class:`int`
    """

    if not class_list:
        raise ValueError('at least one property required')

    query = '''SELECT DISTINCT
        count(?subject)
    WHERE {{
        {classes}
    }}'''.format(classes=' UNION '.join('{ ?subject a %s . }'
                                        % x for x in class_list))

    cnt = select_dbpedia(query)
    if cnt:
        return int(cnt[0]['callret-0'])
    else:
        return 0


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

    query = '''SELECT DISTINCT
        ?{s_name}
        ?{s_name}_label
        ?{o_name}
        ?{o_name}_label
        ?revision
    WHERE {{
        ?{s_name} ?p ?{o_name} .
        OPTIONAL {{ ?{s_name} rdfs:label ?{s_name}_label .
                FILTER langMatches( lang(?{s_name}_label), "EN" ) . }}
        OPTIONAL {{ ?{o_name} rdfs:label ?{o_name}_label .
                FILTER langMatches( lang(?{o_name}_label), "EN" ) . }}
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
        filt=' || '.join('?p = %s\n' % x for x in p),
        limit=PAGE_ITEM_COUNT,
        offset=PAGE_ITEM_COUNT * page,
        revision=revision,
    )
    return select_dbpedia(query)


def parse_entity(entity):
    if ':' in entity:
        if ':' in entity:
            col_name = entity.split(':')[1]
        if '/' in entity:
            col_name = entity.split('/')[1]
    else:
        col_name = entity[:3]
    return col_name


def select_by_class(s, s_name='subject',  p={}, entities=[], page=1):
    """List of **s** which as property as **entities**

    :param str s: Ontology name of subject.
    :param str s_name: Name of subject. It doesn't affect the results.
    :param list entities: List of property ontologies.
    :param page: The offset of query, each page will return 100 entities.
    :type page: :class:`int`
    :return: list of a dict mapping keys which have 'entities' as property.
    :rtype: :class:`list`

    For example::

        select_by_class (
            s_name='author',
            s=['dbpedia-owl:Artist', 'dbpedia-owl:ComicsCreator'],
            p=['dbpedia-owl:author', 'dbpprop:author', 'dbpedia-owl:writer'],
            entities=['dbpedia-owl:birthDate', 'dbpprop:shortDescription']
        )


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

    query = '''SELECT DISTINCT
        ?{s_name}
        {entities}
        WHERE {{
            {is_in_class}
            {has_property}
            {optional_properties}
        }}
        GROUP BY ?{s_name}
        LIMIT {limit}
        OFFSET {offset}'''.format(
        s_name=s_name,
        entities='\n'.join('?%s'
                           % parse_entity(entity) for entity in entities),
        is_in_class=' UNION '.join('{ ?%s a %s . }\n'
                                   % (s_name, x) for x in s),
        has_property=''.join('UNION { ?%s %s ?prop . }\n'
                             % (s_name, prop) for prop in p),
        optional_properties=''.join('OPTIONAL { ?%s %s ?%s . }\n'
                                    % (s_name, entity, parse_entity(entity))
                                    for entity in entities),
        limit=PAGE_ITEM_COUNT,
        offset=PAGE_ITEM_COUNT * page
    )
    query = query.replace('?label . ',
                          '?label .  filter langMatches( lang(?label), "EN" )')

    return select_dbpedia(query)


@app.task
def fetch_classes(page, object_, identity):
    logger = get_task_logger(__name__ + '.fetch_classes')
    session = get_session()
    res = select_by_class(
        s=identity,
        s_name='name',
        entities=object_.PROPERTIES,
        page=page,
        p=object_.TYPE_PREDICATES,
    )

    current_time = datetime.datetime.now(datetime.timezone.utc)
    logger.warning('fetching %s, %d', identity, len(res))
    for item in res:
        try:
            with session.begin():
                new_entity = object_.initialize(item)
                new_entity.last_crawled = current_time
                new_entity = session.merge(new_entity)
                session.add(new_entity)
        except IntegrityError:
            entities = session.query(object_) \
                .filter_by(
                    name=item['name']
                )
            if entities.count() > 0:
                entity = entities.one()
                entity.last_crawled = current_time
                entity.initalize(item)


def crawl_classes(identity):
    entity_num = count_by_class(identity)
    sql_classes = {
        'dbpedia-owl:Artist': Artist,
        'dbpedia-owl:Book': Book,
        'dbpedia-owl:Entity': Entity,
        'dbpedia-owl:Film': Film,
        'dbpedia-owl:Relation': Relation,
        'dbpedia-owl:Work': Work
    }

    for x in range(0, entity_num // PAGE_ITEM_COUNT + 1):
        fetch_classes(x, sql_classes.get(identity[0], Entity), identity)


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
        with session.begin():
            new_entity = Relation(
                work=item.get('work', ''),
                work_label=item.get('work_label', ''),
                author=item.get('author', ''),
                author_label=item.get('author_label', ''),
                revision=item.get('revision', ''),
            )
            session.add(new_entity)

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

    crawl_classes(['dbpedia-owl:Artist'])
    crawl_classes(['dbpedia-owl:Book', 'dbpedia-owl:Novel'])
    crawl_classes(['dbpedia-owl:Cartoon'])
    crawl_classes(['dbpedia-owl:Film'])
    crawl_classes(['dbpedia-owl:Work'])
