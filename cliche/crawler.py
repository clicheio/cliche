from __future__ import print_function

from datetime import datetime, timedelta
import sys
import urllib.parse

from celery.utils.log import get_task_logger
from lxml.html import parse
import psycopg2

from .worker import worker


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
    conn = psycopg2.connect(worker.conf.DB_FILENAME)
    cur = conn.cursor()
    try:
        cur.execute('INSERT INTO indexindex VALUES (%s, %s, %s, NULL)',
                    (name[0], name[1], url))
    except psycopg2.IntegrityError:
        cur.execute('UPDATE indexindex SET url = %s '
                    'WHERE namespace = %s and name = %s',
                    (url, name[0], name[1]))
        conn.rollback()
    conn.commit()
    cur.execute('SELECT count(*) FROM indexindex')
    get_task_logger(__name__ + '.save_link').info(
        'Total %d',
        cur.fetchone()[0]
    )


@worker.task
def crawl_link(namespace, name, url, referer, start_time,
               start_indexindex_count, start_relations_count,
               round_count):
    conn = psycopg2.connect(worker.conf.DB_FILENAME)
    c = conn.cursor()
    logger = get_task_logger(__name__ + '.crawl_link')
    current_time = datetime.now()
    tree = parse(url)
    try:
        namespace = tree.xpath('//div[@class="pagetitle"]')[0] \
            .text.strip()[:-1]
    except (AttributeError, AssertionError, IndexError):
        logger.warning('Warning: There is no pagetitle on this page. '
                       'Ignoring.')
        return
    if namespace == '':
        namespace = 'Main'
    name = tree.xpath('//div[@class="pagetitle"]/span')[0].text.strip()
    logger.info("Fetching: {}/{} @ {}"
                .format(namespace, name, url))
    c.execute('SELECT count(*) FROM indexindex '
              'WHERE namespace = %s and name = %s',
              (namespace, name))
    if cur.fetchone()[0] != 0:
        c.execute('SELECT last_crawled FROM indexindex '
                  'WHERE namespace = %s and name = %s',
                  (namespace, name))
        last_crawled = c.fetchone()
        if last_crawled and last_crawled[0]:
            if (current_time - last_crawled[0]) < CRAWL_INTERVAL:
                logger.info('Skipping: {}/{} @ {} due to'
                            'recent crawl in {} days'
                            .format(namespace, name, url, CRAWL_INTERVAL))
                return
    else:
        try:
            c.execute('INSERT INTO indexindex VALUES (%s, %s, %s, %s)',
                      (namespace, name, url, None))
        except psycopg2.IntegrityError:
            conn.rollback()
    conn.commit()
    for a in tree.xpath('//a[@class="twikilink"]'):
        try:
            destination_name = a.text.strip()
            destination_url = urllib.parse.urljoin(
                WIKI_PAGE, a.attrib['href']
            )
            # FIXME if next_crawl not in crawl_stack:
            crawl_link.delay(None, destination_name, destination_url,
                             (namespace, name), start_time,
                             start_indexindex_count, start_relations_count,
                             round_count)
        except AttributeError:
            pass
    if referer is not None:
        try:
            c.execute('INSERT INTO relations VALUES (%s, %s, %s, %s)',
                      (referer[0], referer[1], namespace, name))
        except psycopg2.IntegrityError:
            conn.rollback()
    logger.info('Crawling {}/{} @ {} completed at {}'
                .format(namespace, name, url, current_time))
    c.execute('''
        UPDATE indexindex SET last_crawled = %s
        WHERE namespace = %s and name = %s
            ''', (current_time, namespace, name))
    round_count += 1
    if round_count >= 10:
        round_count = 0
        elasped = datetime.now() - start_time
        elasped_hours = elasped.total_seconds() / 3600
        c.execute('SELECT count(*) FROM indexindex')
        indexindex_count = int(c.fetchone()[0]) - start_indexindex_count
        c.execute('SELECT count(*) FROM relations')
        relations_count = int(c.fetchone()[0]) - start_relations_count
        logger.info('-> indexindex: %s (%s/h) relations: %s (%s/h) '
                    'elasped %s',
                    indexindex_count,
                    int(indexindex_count / elasped_hours),
                    relations_count,
                    int(relations_count / elasped_hours),
                    elasped)


def initialize(connection):
    cur = connection.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS indexindex
        (
        namespace text, name text, url text, last_crawled timestamp,
        constraint pk_indexindex primary key(namespace, name)
        )
    ''')
    connection.commit()
    cur.execute('SELECT count(*) FROM indexindex')
    if cur.fetchone()[0] < 1:
        for name, url in list_pages():
            save_link.delay(name, url)
    # FIXME
    cur.execute('SELECT count(*) FROM indexindex')
    print('Total', cur.fetchone()[0])


def crawl(connection):
    cur = connection.cursor()
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
    initialize(connection)
    cur.execute('SELECT namespace, name, url FROM indexindex '
                'ORDER BY namespace asc, name asc')
    seed = cur.fetchall()
    start_time = datetime.now()
    cur.execute('SELECT count(*) FROM indexindex')
    start_indexindex_count = int(cur.fetchone()[0])
    cur.execute('SELECT count(*) FROM relations')
    start_relations_count = int(cur.fetchone()[0])
    round_count = 0
    for namespace, name, url in seed:
        crawl_link.delay(namespace, name, url, None, start_time,
                         start_indexindex_count, start_relations_count,
                         round_count)
    connection.commit()


def load_config(filename):
    with open(filename) as f:
        code = compile(f.read(), filename, 'exec')
    loc = {}
    exec(code, globals(), loc)
    return loc


general_help_string = '''
Usage: python crawler.py <command> <arguments>

commands:

    init:
        Usage: python crawler.py init <config-file>

        Crawls indexindex of TVTropes.
        If an entry already exists, it is updated to new url.
        If the process is inturruped in the middle, nothing will be saved.

    relation:
        Usage: python crawler.py relation <config-file>

        Crawls each pages and saves it to a table, using items in
        indexindex table as seeds. New pages are saved to indexindex table,
        and relationship of pages are saved to relations table.
        If indexindex table is not found, an error will be raised.

If a db file is not already present with each commands, one will be
automatically created.
'''.strip()


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == 'init':
            if len(sys.argv) != 3:
                print('Usage: python crawler.py init <config-file>',
                      file=sys.stderr)
                raise SystemExit(1)
            config_file = sys.argv[2]
            config = load_config(config_file)
            worker.config_from_object(config)
            db_file = config['DB_FILENAME']
            conn = psycopg2.connect(db_file)
            initialize(conn)
        elif sys.argv[1] == 'relation':
            if len(sys.argv) != 3:
                print('Usage: python crawler.py relation <config-file>',
                      file=sys.stderr)
                raise SystemExit(1)
            config_file = sys.argv[2]
            config = load_config(config_file)
            worker.config_from_object(config)
            db_file = config['DB_FILENAME']
            conn = psycopg2.connect(db_file)
            crawl(conn)
        else:
            print(general_help_string, file=sys.stderr)
            raise SystemExit(1)
    else:
        print(general_help_string, file=sys.stderr)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
