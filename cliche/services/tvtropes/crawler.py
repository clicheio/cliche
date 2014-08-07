from __future__ import print_function

from argparse import ArgumentParser
from datetime import datetime, timedelta
import urllib.parse

from celery.utils.log import get_task_logger
from lxml.html import parse
import psycopg2

from ...worker import worker


INDEX_INDEX = 'http://tvtropes.org/pmwiki/index_report.php'
WIKI_PAGE = 'http://tvtropes.org/pmwiki/pmwiki.php/'
CRAWL_INTERVAL = timedelta(days=7)


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
def save_link(name, url):
    with psycopg2.connect(worker.conf.DB_FILENAME) as conn:
        cur = conn.cursor
        try:
            type = 'Trope' if name[0] == 'Main' else 'Work'
            cur.execute('INSERT INTO entities VALUES (%s, %s, %s, NULL, %s)',
                        (name[0], name[1], url, type))
        except psycopg2.IntegrityError:
            cur.execute('UPDATE entities SET url = %s '
                        'WHERE namespace = %s and name = %s',
                        (url, name[0], name[1]))
            conn.rollback()
        conn.commit()
        cur.execute('SELECT count(*) FROM entities')
        get_task_logger(__name__ + '.save_link').info(
            'Total %d',
            cur.fetchone()[0]
        )


def fetch_link(url, conn, cur):
    tree = parse(url)
    try:
        namespace = tree.xpath('//div[@class="pagetitle"]')[0] \
            .text.strip()[:-1]
    except (AttributeError, AssertionError, IndexError):
        return None
    if namespace == '':
        namespace = 'Main'
    name = tree.xpath('//div[@class="pagetitle"]/span')[0].text.strip()
    try:
        type = 'Trope' if namespace == 'Main' else 'Work'
        cur.execute('INSERT INTO entities VALUES (%s, %s, %s, NULL, %s)',
                    (namespace, name, url, type))
    except psycopg2.IntegrityError:
        conn.rollback()
    conn.commit()
    return tree, namespace, name


@worker.task
def crawl_link(url, start_time,
               start_indexindex_count, start_relations_count,
               round_count):
    with psycopg2.connect(worker.conf.DB_FILENAME) as conn:
        cur = conn.cursor()
        logger = get_task_logger(__name__ + '.crawl_link')
        current_time = datetime.now()

        cur.execute('SELECT last_crawled FROM entities '
                    'WHERE url = %s',
                    (url,))
        last_crawled = cur.fetchone()
        if last_crawled and last_crawled[0]:
            if (current_time - last_crawled[0]) < CRAWL_INTERVAL:
                logger.info('Skipping: {} due to '
                            'recent crawl in {} days'
                            .format(url, CRAWL_INTERVAL))
                conn.close()
                return

        fetch_result = fetch_link(url, conn, cur)
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
                fetch_result = fetch_link(url, conn, cur)
                if fetch_result is None:
                    logger.warning('Warning: There is no pagetitle on '
                                   'this page. Ignoring.')
                    return
                destination_tree, destination_namespace, \
                    destination_name = fetch_result
                try:
                    cur.execute('INSERT INTO relations VALUES '
                                '(%s, %s, %s, %s)',
                                (namespace, name,
                                 destination_namespace,
                                 destination_name))
                except psycopg2.IntegrityError:
                    conn.rollback()
                # FIXME if next_crawl not in crawl_stack:
                crawl_link.delay(destination_url, start_time,
                                 start_indexindex_count, start_relations_count,
                                 round_count)
            except AttributeError:
                pass
        logger.info('Crawling {}/{} @ {} completed at {}'
                    .format(namespace, name, url, current_time))
        cur.execute('''
            UPDATE entities SET last_crawled = %s
            WHERE namespace = %s and name = %s
                ''', (current_time, namespace, name))
        round_count += 1
        if round_count >= 10:
            round_count = 0
            elasped = datetime.now() - start_time
            elasped_hours = elasped.total_seconds() / 3600
            cur.execute('SELECT count(*) FROM entities')
            indexindex_count = int(cur.fetchone()[0]) - start_indexindex_count
            cur.execute('SELECT count(*) FROM relations')
            relations_count = int(cur.fetchone()[0]) - start_relations_count
            logger.info('-> entities: %s (%s/h) relations: %s (%s/h) '
                        'elasped %s',
                        indexindex_count,
                        int(indexindex_count / elasped_hours),
                        relations_count,
                        int(relations_count / elasped_hours),
                        elasped)


def crawl(connection):
    with connection.cursor() as cur:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS entities
            (
            namespace text, name text, url text, last_crawled timestamp,
            type text,
            constraint pk_entities primary key(namespace, name)
            )
        ''')
        connection.commit()
        cur.execute('SELECT count(*) FROM entities')
        if cur.fetchone()[0] < 1:
            for name, url in list_pages():
                save_link.delay(name, url)

        cur.execute('''
            CREATE TABLE IF NOT EXISTS relations
            (
            origin_namespace text, origin text,
            destination_namespace text, destination text,
            constraint pk_relations primary key(origin_namespace, origin,
            destination_namespace, destination)
            )
            ''')
        connection.commit()
        cur.execute('SELECT namespace, name, url FROM entities '
                    'ORDER BY namespace asc, name asc')
        seed = cur.fetchall()
        start_time = datetime.now()
        cur.execute('SELECT count(*) FROM entities')
        start_indexindex_count = int(cur.fetchone()[0])
        cur.execute('SELECT count(*) FROM relations')
        start_relations_count = int(cur.fetchone()[0])
        round_count = 0
        for namespace, name, url in seed:
            crawl_link.delay(url, None, start_time,
                             start_indexindex_count, start_relations_count,
                             round_count)
        connection.commit()


def load_config(filename):
    with open(filename) as f:
        code = compile(f.read(), filename, 'exec')
    loc = {}
    exec(code, globals(), loc)
    return loc


def main():
    parser = ArgumentParser(
        description='Crawles TVTropes and saves metadata.'
    )
    parser.add_argument('config_file')
    args = parser.parse_args()

    config = load_config(args.config_file)
    worker.config_from_object(config)
    db_file = config['DB_FILENAME']
    with psycopg2.connect(db_file) as conn:
        crawl(conn)


if __name__ == '__main__':
    main()
