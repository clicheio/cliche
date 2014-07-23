from __future__ import print_function

from datetime import datetime, timedelta
import sys
import sqlite3
import urllib.parse

from celery.utils.log import get_task_logger
from lxml.html import parse

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
    conn = sqlite3.connect(worker.conf.DB_FILENAME,
                           detect_types=sqlite3.PARSE_DECLTYPES)
    cur = conn.cursor()
    try:
        cur.execute('INSERT INTO indexindex VALUES (?, ?, ?, NULL)',
                    (name[0], name[1], url))
    except sqlite3.IntegrityError:
        cur.execute('UPDATE indexindex SET url = ? '
                    'WHERE namespace = ? and name = ?',
                    (url, name[0], name[1]))
    conn.commit()
    get_task_logger(__name__ + '.save_link').info(
        'Total %d',
        cur.execute('SELECT count(*) FROM indexindex').fetchone()[0]
    )


@worker.task
def crawl_link(namespace, name, url, referer, start_time,
               start_indexindex_count, start_relations_count,
               round_count):
    conn = sqlite3.connect(worker.conf.DB_FILENAME,
                           detect_types=sqlite3.PARSE_DECLTYPES)
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
    if c.execute('SELECT count(*) FROM indexindex '
                 'WHERE namespace = ? and name = ?',
                 (namespace, name)).fetchone()[0] != 0:
        last_crawled = c.execute('SELECT last_crawled FROM indexindex '
                                 'WHERE namespace = ? and name = ?',
                                 (namespace, name)).fetchone()
        if last_crawled and last_crawled[0]:
            if (current_time - last_crawled[0]) < CRAWL_INTERVAL:
                logger.info('Skipping: {}/{} @ {} due to'
                            'recent crawl in {} days'
                            .format(namespace, name, url, CRAWL_INTERVAL))
                return
    else:
        try:
            c.execute('INSERT INTO indexindex VALUES (?, ?, ?, ?)',
                      (namespace, name, url, None))
        except sqlite3.IntegrityError:
            pass
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
            c.execute('INSERT INTO relations VALUES (?, ?, ?, ?)',
                      (referer[0], referer[1], namespace, name))
        except sqlite3.IntegrityError:
            pass
    logger.info('Crawling {}/{} @ {} completed at {}'
                .format(namespace, name, url, current_time))
    c.execute('''
        UPDATE indexindex SET last_crawled = ?
        WHERE namespace = ? and name = ?
            ''', (current_time, namespace, name))
    round_count += 1
    if round_count >= 10:
        round_count = 0
        elasped = datetime.now() - start_time
        elasped_hours = elasped.total_seconds() / 3600
        indexindex_count = int(
            c.execute('SELECT count(*) FROM indexindex')
            .fetchone()[0]) - start_indexindex_count
        relations_count = int(
            c.execute('SELECT count(*) FROM relations')
            .fetchone()[0]) - start_relations_count
        logger.info('-> indexindex: {} ({}/h) relations: {} ({}/h) '
                    'elasped {}'
                    .format(indexindex_count,
                            int(indexindex_count / elasped_hours),
                            relations_count,
                            int(relations_count / elasped_hours),
                            elasped))


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
    for name, url in list_pages():
        save_link.delay(name, url)
    # FIXME
    print('Total',
          cur.execute('SELECT count(*) FROM indexindex').fetchone()[0])


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
    if cur.execute("SELECT name FROM sqlite_master "
                   "WHERE name='indexindex'").fetchone() is None:
        initialize(connection)
    seed = cur.execute('SELECT namespace, name, url FROM indexindex '
                       'ORDER BY namespace asc, name asc').fetchall()
    start_time = datetime.now()
    start_indexindex_count = int(
        cur.execute('SELECT count(*) FROM indexindex')
        .fetchone()[0])
    start_relations_count = int(
        cur.execute('SELECT count(*) FROM relations')
        .fetchone()[0])
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
            conn = sqlite3.connect(db_file,
                                   detect_types=sqlite3.PARSE_DECLTYPES)
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
            conn = sqlite3.connect(db_file,
                                   detect_types=sqlite3.PARSE_DECLTYPES)
            crawl(conn)
        else:
            print(general_help_string, file=sys.stderr)
            raise SystemExit(1)
    else:
        print(general_help_string, file=sys.stderr)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
