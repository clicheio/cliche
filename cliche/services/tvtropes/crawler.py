""":mod:`cliche.services.tvtropes.crawler` --- TVTropes_ crawler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. _TVTropes: http://tvtropes.org/

"""
from __future__ import print_function

import datetime
import urllib.parse

from celery.utils.log import get_task_logger
from lxml.html import document_fromstring, parse
import requests
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import FlushError, NoResultFound

from ...celery import app, get_session
from .entities import Entity, Redirection, Relation


BASE_URL = 'http://tvtropes.org/pmwiki/'
INDEX_INDEX = urllib.parse.urljoin(BASE_URL, 'index_report.php')
WIKI_PAGE = urllib.parse.urljoin(BASE_URL, 'pmwiki.php/')
RELATED_SEARCH = urllib.parse.urljoin(BASE_URL, 'relatedsearch.php?term=')

CRAWL_INTERVAL = datetime.timedelta(days=7)


def determine_type(namespace):
    if namespace == 'Main':
        return 'Trope'
    elif namespace == 'Administrivia':
        return 'Administrivia'
    else:
        return 'Work'


def list_pages(namespace_url=None):
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

        for a in namespaces:
            if "index_report.php?groupname=Administrivia" in a.attrib['href']:
                continue
            url = urllib.parse.urljoin(
                INDEX_INDEX, a.attrib['href']
            )
            for value in list_pages(url):
                yield value


def upsert_entity(session, namespace, name, type, url):
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
            entity.type = type


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
        name_path = '//div[@class="pagetitle"]/div[@class="article_title"]/h1'
        name = tree.xpath(name_path)[0].text.strip()
    except (AttributeError, AssertionError, IndexError):
        logger.warning('no name in %s', final_url)
        return False, tree, None, None, final_url
    else:
        (namespace, name) = map(lambda x: x.strip(), name.split(':'))
        namespace = 'Main' if namespace == '' else namespace
        type = determine_type(namespace)
        if type == 'Administrivia':
            return False, tree, namespace, name, final_url
        upsert_entity(session, namespace, name, type, final_url)
        process_redirections(session, url, final_url, namespace, name)
        return True, tree, namespace, name, final_url


def recently_crawled(current_time, url, session):
    logger = get_task_logger(__name__ + '.recently_crawled')
    try:
        last_crawled = session.query(Entity).filter_by(url=url) \
                              .one().last_crawled
        if last_crawled:
            if current_time - last_crawled < CRAWL_INTERVAL:
                logger.info('%s was recently crawled in %s days.',
                            url, CRAWL_INTERVAL)
                return True
    except NoResultFound:
        pass
    return False


def is_wiki_page(url):
    return (BASE_URL not in url or WIKI_PAGE in url)


@app.task
def crawl_link(url):
    session = get_session()
    logger = get_task_logger(__name__ + '.crawl_link')
    current_time = datetime.datetime.now(datetime.timezone.utc)
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
                destination_name, destination_url = fetch_link(
                    destination_url,
                    session,
                    log_prefix='(child) '
                )
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


@app.task
def crawl():
    session = get_session()
    if session.query(Entity).count() < 1:
        seeds = list(list_pages())
        for url in seeds:
            crawl_link.delay(url)
    else:
        for entity in session.query(Entity) \
                             .order_by(Entity.namespace, Entity.name):
            crawl_link.delay(entity.url)
