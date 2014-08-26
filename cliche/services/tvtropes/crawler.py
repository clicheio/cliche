""":mod:`cliche.services.tvtropes.crawler` --- TVTropes_ crawler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. _TVTropes: http://tvtropes.org/

"""
from __future__ import print_function

from datetime import datetime, timedelta
import urllib.parse

import requests

from celery.signals import worker_process_init
from celery.utils.log import get_task_logger
from lxml.html import document_fromstring, parse
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import FlushError, NoResultFound

from .entities import Entity, Redirection, Relation
from ...orm import Base, Session
from ...worker import worker


BASE_URL = 'http://tvtropes.org/pmwiki/'
INDEX_INDEX = urllib.parse.urljoin(BASE_URL, 'index_report.php')
WIKI_PAGE = urllib.parse.urljoin(BASE_URL, 'pmwiki.php/')
RELATED_SEARCH = urllib.parse.urljoin(BASE_URL, 'relatedsearch.php?term=')

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


def list_pages(namespace_url=None, *, print_callback=None):
    list_url = namespace_url or INDEX_INDEX
    tree = parse(list_url)

    for a in tree.xpath('//a[@class="twikilink"]'):
        url = a.attrib['href']
        if WIKI_PAGE in url:
            yield url

    if not namespace_url:
        namespaces = tree.xpath(
            '//a[starts-with(@href, "index_report.php?groupname=")]'
        )
        if print_callback is not None:
            print_callback(' {} more.'.format(len(namespaces)), flush=True)

        count = 0
        for a in namespaces:
            count += 1
            if count % 10 == 0:
                if print_callback is not None:
                    print_callback('/', end="", flush=True)
            else:
                if print_callback is not None:
                    print_callback('.', end="", flush=True)
            if "index_report.php?groupname=Administrivia" in a.attrib['href']:
                continue
            url = urllib.parse.urljoin(
                INDEX_INDEX, a.attrib['href']
            )
            for value in list_pages(url, print_callback=print_callback):
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
            if alias_namespace == 'Administrivia':
                continue
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


def fetch_link(url, session, *, log_prefix=''):
    '''Returns result, tree, namespace, name, final_url.'''
    logger = get_task_logger(__name__ + '.fetch_link')
    if not is_wiki_page(url):
        return False, None, None, None, url
    r = requests.get(url)
    try:
        final_url = r.url[:r.url.index('?')]
    except ValueError:
        final_url = r.url
    if not is_wiki_page(final_url):
        return False, None, None, None, final_url
    tree = document_fromstring(r.text)
    try:
        namespace = tree.xpath('//div[@class="pagetitle"]')[0] \
            .text.strip()[:-1]
    except (AttributeError, AssertionError, IndexError):
        logger.warning('%sWarning on url %s: '
                       'There is no pagetitle on this page. Ignoring.',
                       log_prefix, url)
        return False, tree, None, None, final_url
    if namespace == '':
        namespace = 'Main'
    name = tree.xpath('//div[@class="pagetitle"]/span')[0].text.strip()

    type = determine_type(namespace)
    if type == 'Administrivia':
        return False, tree, namespace, name, final_url
    new_or_update_entity(session, namespace, name, type, final_url)
    process_redirections(session, url, final_url, namespace, name)
    return True, tree, namespace, name, final_url


def recently_crawled(current_time, url, session):
    logger = get_task_logger(__name__ + '.recently_crawled')
    try:
        last_crawled = session.query(Entity).filter_by(url=url) \
                              .one().last_crawled
        if last_crawled:
            if current_time.replace(tzinfo=None) - \
               last_crawled.replace(tzinfo=None) < CRAWL_INTERVAL:
                logger.info('%s was recently crawled in %s days.',
                            url, CRAWL_INTERVAL)
                return True
    except NoResultFound:
        pass
    return False


def is_wiki_page(url):
    return (BASE_URL not in url or WIKI_PAGE in url)


@worker.task
def crawl_link(url):
    global db_engine
    session = Session(bind=db_engine)
    logger = get_task_logger(__name__ + '.crawl_link')
    current_time = datetime.now()
    if recently_crawled(current_time, url, session):
        return
    result, tree, namespace, name, url = fetch_link(url, session)
    if not result:
        return
    # make sure that if redirected, final url is not also recently crawled.
    if recently_crawled(current_time, url, session):
        return
    logger.info("Fetching: %s/%s @ %s", namespace, name, url)
    for a in tree.xpath('//div[@id="wikitext"]//a[@class="twikilink"]'):
        try:
            destination_url = urllib.parse.urljoin(
                WIKI_PAGE, a.attrib['href']
            )
            destination_result, destination_tree, destination_namespace, \
                destination_name, destination_type, \
                destination_url = fetch_link(destination_url, session,
                                             log_prefix='(child) ')
            if not result:
                return
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
    logger.info('Crawling %s/%s @ %s completed at %s',
                namespace, name, url, current_time)
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
        print('Populating seeds...', end="", flush=True)
        for url in list_pages(print_callback=print):
            crawl_link.delay(url)
    else:
        for entity in session.query(Entity) \
                             .order_by(Entity.namespace, Entity.name):
            crawl_link.delay(entity.url)
