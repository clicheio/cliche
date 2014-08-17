""":mod:`cliche.services.tvtropes.crawler` --- TVTropes_ crawler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. _TVTropes: http://tvtropes.org/

"""
from __future__ import print_function

from datetime import datetime, timedelta
import urllib.parse

from celery.utils.log import get_task_logger
from lxml.html import parse
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError

from .entities import Entity, Relation
from ...orm import Base, Session
from ...worker import worker


INDEX_INDEX = 'http://tvtropes.org/pmwiki/index_report.php'
WIKI_PAGE = 'http://tvtropes.org/pmwiki/pmwiki.php/'
CRAWL_INTERVAL = timedelta(days=7)


def determine_type(namespace):
    return 'Trope' if namespace == 'Main' else 'Work'


def list_pages(namespace_url=None):
    list_url = namespace_url or INDEX_INDEX
    print('Crawling {}'.format(list_url))
    tree = parse(list_url)

    for a in tree.xpath('//a[@class="twikilink"]'):
        name = a.text.strip()
        url = a.attrib['href']
        if namespace_url:
            yield (name,), url
        else:
            yield ('Main', name), url

    if not namespace_url:
        namespaces = tree.xpath(
            '//a[starts-with(@href, "index_report.php?groupname=")]'
        )

        for a in namespaces:
            namespace = a.text.strip()
            url = urllib.parse.urljoin(
                INDEX_INDEX, a.attrib['href']
            )
            for key, value in list_pages(url):
                assert len(key) == 1
                yield (namespace,) + key, value


@worker.task
def save_link(namepair, url):
    namespace, name = namepair
    engine = create_engine(worker.conf.DATABASE_URL)
    session = Session(bind=engine)
    try:
        with session.begin():
            new_entity = Entity(
                namespace=namespace,
                name=name,
                url=url,
                type=determine_type(namespace)
            )
            session.add(new_entity)
    except IntegrityError:
        with session.begin():
            entity = session.query(Entity) \
                            .filter_by(namespace=namespace, name=name) \
                            .one()
            entity.url = url
    get_task_logger(__name__ + '.save_link').info(
        'Total %d',
        session.query(Entity).count()
    )


def fetch_link(url, session):
    tree = parse(url)
    try:
        namespace = tree.xpath('//div[@class="pagetitle"]')[0] \
            .text.strip()[:-1]
    except (AttributeError, AssertionError, IndexError):
        return None
    if namespace == '':
        namespace = 'Main'
    name = tree.xpath('//div[@class="pagetitle"]/span')[0].text.strip()
    with session.begin():
        new_entity = Entity(
            namespace=namespace,
            name=name,
            url=url,
            type=determine_type(namespace)
        )
        session.add(new_entity)
    return tree, namespace, name


@worker.task
def crawl_link(url, start_time,
               start_indexindex_count, start_relations_count,
               round_count):
    engine = create_engine(worker.conf.DATABASE_URL)
    session = Session(bind=engine)
    logger = get_task_logger(__name__ + '.crawl_link')
    current_time = datetime.now()

    last_crawled = session.query(Entity).filter_by(url=url) \
                          .first().last_crawled
    if last_crawled:
        if current_time - last_crawled < CRAWL_INTERVAL:
            logger.info('Skipping: {} due to '
                        'recent crawl in {} days'
                        .format(url, CRAWL_INTERVAL))
            return

    fetch_result = fetch_link(url, session)
    if fetch_result is None:
        logger.warning('Warning: There is no pagetitle on this page. '
                       'Ignoring.')
        return
    tree, namespace, name = fetch_result
    logger.info("Fetching: {}/{} @ {}"
                .format(namespace, name, url))
    for a in tree.xpath('//a[@class="twikilink"]'):
        try:
            destination_url = urllib.parse.urljoin(
                WIKI_PAGE, a.attrib['href']
            )
            fetch_result = fetch_link(url, session)
            if fetch_result is None:
                logger.warning('Warning: There is no pagetitle on '
                               'this page. Ignoring.')
                return
            destination_tree, destination_namespace, \
                destination_name = fetch_result
            with session.begin():
                new_relation = Relation(
                    origin_namespace=namespace,
                    origin_name=name,
                    destination_namespace=destination_namespace,
                    destination_name=destination_name
                )
                session.add(new_relation)
            # FIXME if next_crawl not in crawl_stack:
            crawl_link.delay(destination_url, start_time,
                             start_indexindex_count, start_relations_count,
                             round_count)
        except AttributeError:
            pass
    logger.info('Crawling {}/{} @ {} completed at {}'
                .format(namespace, name, url, current_time))
    with session.begin():
        entity = session.query(Entity) \
                        .filter_by(url=url) \
                        .one()
        entity.last_crawled = current_time
    round_count += 1
    if round_count >= 10:
        round_count = 0
        elasped = datetime.now() - start_time
        elasped_hours = elasped.total_seconds() / 3600
        indexindex_count = session.query(Entity).count() \
            - start_indexindex_count
        relations_count = session.query(Relation).count() \
            - start_relations_count
        logger.info('-> entities: %s (%s/h) relations: %s (%s/h) '
                    'elasped %s',
                    indexindex_count,
                    int(indexindex_count / elasped_hours),
                    relations_count,
                    int(relations_count / elasped_hours),
                    elasped)


def crawl(config):
    worker.config_from_object(config)
    engine = create_engine(worker.conf.DATABASE_URL)
    session = Session(bind=engine)

    Base.metadata.create_all(engine)
    if session.query(Entity).count() < 1:
        for name, url in list_pages():
            save_link.delay(name, url)

    for entity in session.query(Entity) \
                         .order_by(Entity.namespace, Entity.name):
        crawl_link.delay(entity.url, datetime.now(),
                         session.query(Entity).count(),
                         session.query(Relation).count(),
                         0)
