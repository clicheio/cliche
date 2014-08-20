from __future__ import print_function

from datetime import datetime, timedelta
import urllib.parse

import requests

from celery.signals import worker_process_init
from celery.utils.log import get_task_logger
from lxml.html import parse, document_fromstring
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import FlushError, NoResultFound

from .entities import Entity, Relation, Redirection
from ...orm import Base, Session
from ...worker import worker


INDEX_INDEX = 'http://tvtropes.org/pmwiki/index_report.php'
WIKI_PAGE = 'http://tvtropes.org/pmwiki/pmwiki.php/'
RELATED_SEARCH = 'http://tvtropes.org/pmwiki/relatedsearch.php?term='

CRAWL_INTERVAL = timedelta(days=7)


db_engine = None


@worker_process_init.connect
def establish_database_connection(*args, **kwargs):
    global db_engine
    db_engine = create_engine(worker.conf.DATABASE_URL)


def determine_type(namespace):
    if namespace == 'Main':
        return 'Trope'
    elif namespace == 'Administrivia':
        return 'Administrivia'
    else:
        return 'Work'


def list_pages(namespace_url=None):
    list_url = namespace_url or INDEX_INDEX
    print('Populating seed from {}'.format(list_url))
    tree = parse(list_url)

    for a in tree.xpath('//a[@class="twikilink"]'):
        url = a.attrib['href']
        yield url

    if not namespace_url:
        namespaces = tree.xpath(
            '//a[starts-with(@href, "index_report.php?groupname=")]'
        )

        for a in namespaces:
            url = urllib.parse.urljoin(
                INDEX_INDEX, a.attrib['href']
            )
            for value in list_pages(url):
                yield value


def new_or_update_entity(session, namespace, name, type, url):
    try:
        with session.begin():
            new_entity = Entity(
                namespace=namespace,
                name=name,
                url=url,
                type=type
            )
            session.add(new_entity)
    except (FlushError, IntegrityError):
        with session.begin():
            entity = session.query(Entity) \
                            .filter_by(namespace=namespace, name=name) \
                            .one()
            entity.url = url


def process_redirections(session, original_url, final_url, namespace, name):
    # note that indirection is not considered:
    # only the original and final path are saved.
    *_, original_path = urllib.parse.urlparse(original_url).path.split('/', 3)
    *_, final_path = urllib.parse.urlparse(final_url).path.split('/', 3)
    if original_path != final_path:
        rel = requests.get(RELATED_SEARCH + final_path)
        reltree = document_fromstring(rel.text)
        for link in reltree.xpath(
            "//div[@id='wikimiddle']/div[re:test(text(),"
            "'This article is the target of [0-9]+ redirect\(s\)\.'"
            ")]/ul/li/a",
            namespaces={'re': "http://exslt.org/regular-expressions"}
        ):
            alias_namespace = link.text[0:link.text.index('/')]
            alias_name = link.text[link.text.index('/') + 1:]
            try:
                with session.begin():
                    new_redirection = Redirection(
                        alias_namespace=alias_namespace,
                        alias_name=alias_name,
                        original_namespace=namespace,
                        original_name=name
                    )
                    session.add(new_redirection)
            except (FlushError, IntegrityError):
                with session.begin():
                    redirection = session.query(Redirection) \
                        .filter_by(
                            alias_namespace=alias_namespace,
                            alias_name=alias_name
                        ) \
                        .one()
                    redirection.original_namespace = namespace
                    redirection.original_name = name


def fetch_link(url, session):
    r = requests.get(url)
    print(url)
    try:
        final_url = r.url[:r.url.index('?')]
    except ValueError:
        final_url = r.url
    tree = document_fromstring(r.text)
    try:
        namespace = tree.xpath('//div[@class="pagetitle"]')[0] \
            .text.strip()[:-1]
    except (AttributeError, AssertionError, IndexError):
        return False, tree, None, None, '!Lost and Found', final_url
    if namespace == '':
        namespace = 'Main'
    name = tree.xpath('//div[@class="pagetitle"]/span')[0].text.strip()

    type = determine_type(namespace)
    if type == 'Administrivia':
        return False, tree, namespace, name, type, final_url
    new_or_update_entity(session, namespace, name, type, final_url)
    process_redirections(session, url, final_url, namespace, name)
    return True, tree, namespace, name, type, final_url


def recently_crawled(current_time, url, session):
    try:
        last_crawled = session.query(Entity).filter_by(url=url) \
                              .one().last_crawled
        if last_crawled:
            if current_time - last_crawled < CRAWL_INTERVAL:
                return True
    except NoResultFound:
        pass
    return False


@worker.task
def crawl_link(url):
    global db_engine
    session = Session(bind=db_engine)
    logger = get_task_logger(__name__ + '.crawl_link')
    current_time = datetime.now()
    if recently_crawled(current_time, url, session):
        logger.info('Skipping: {} due to '
                    'recent crawl in {} days'
                    .format(url, CRAWL_INTERVAL))
        return
    fetch_result = fetch_link(url, session)
    result, tree, namespace, name, type, url = fetch_result
    if name is None:
        logger.warning('Warning on url {}:'.format(url))
        logger.warning('There is no pagetitle on this page. Ignoring.')
        return
    elif not result:
        logger.warning('Warning on url {}:'.format(url))
        if type == 'Administrivia':
            logger.warning('This page is an Administrivia. Ignoring.')
        elif type == '!Lost and Found':
            logger.warning('This page is a Lost and Found. Ignoring.')
        else:
            logger.warning('This page is not able to be crawled. Ignoring.')
        return
    # make sure that if redirected, final url is not also recently crawled.
    if recently_crawled(current_time, url, session):
        logger.info('Skipping: {} due to '
                    'recent crawl in {} days'
                    .format(url, CRAWL_INTERVAL))
        return
    logger.info("Fetching: {}/{} @ {}"
                .format(namespace, name, url))
    for a in tree.xpath('//a[@class="twikilink"]'):
        try:
            destination_url = urllib.parse.urljoin(
                WIKI_PAGE, a.attrib['href']
            )
            fetch_result = fetch_link(destination_url, session)
            destination_result, destination_tree, destination_namespace, \
                destination_name, destination_type, \
                destination_url = fetch_result
            if destination_name is None:
                logger.warning('Warning on url {} (child):'
                               .format(destination_url))
                logger.warning('There is no pagetitle on this page. Ignoring.')
                continue
            elif not destination_result:
                logger.warning('Warning on url {} (child):'
                               .format(destination_url))
                if destination_type == 'Administrivia':
                    logger.warning('This page is an Administrivia. Ignoring.')
                elif destination_type == '!Lost and Found':
                    logger.warning('This page is a Lost and Found. Ignoring.')
                else:
                    logger.warning('This page is not able '
                                   'to be crawled. Ignoring.')
                continue
            try:
                with session.begin():
                    new_relation = Relation(
                        origin_namespace=namespace,
                        origin_name=name,
                        destination_namespace=destination_namespace,
                        destination_name=destination_name
                    )
                    session.add(new_relation)
            except IntegrityError:
                pass
            # FIXME if next_crawl not in crawl_stack:
            crawl_link.delay(destination_url)
        except AttributeError:
            pass
    logger.info('Crawling {}/{} @ {} completed at {}'
                .format(namespace, name, url, current_time))
    with session.begin():
        entity = session.query(Entity) \
                        .filter_by(url=url) \
                        .one()
        entity.last_crawled = current_time


def crawl(config):
    worker.config_from_object(config)
    global db_engine
    db_engine = create_engine(worker.conf.DATABASE_URL)
    session = Session(bind=db_engine)

    Base.metadata.create_all(db_engine)
    if session.query(Entity).count() < 1:
        for url in list_pages():
            crawl_link.delay(url)
    else:
        for entity in session.query(Entity) \
                             .order_by(Entity.namespace, Entity.name):
            crawl_link.delay(entity.url)
