import sys
import sqlite3
import urllib.parse

from datetime import datetime

from lxml.html import parse


INDEX_INDEX = 'http://tvtropes.org/pmwiki/index_report.php'
WIKI_PAGE = 'http://tvtropes.org/pmwiki/pmwiki.php/'


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


def save_links(links, cur):
    cur.execute('''
        CREATE TABLE IF NOT EXISTS indexindex
        (
        namespace text, name text, url text, last_crawled timestamp,
        constraint pk_indexindex primary key(namespace, name)
        )
    ''')
    for name, url in links:
        try:
            cur.execute('INSERT INTO indexindex VALUES (?, ?, ?, NULL)',
                        (name[0], name[1], url))
        except sqlite3.IntegrityError:
            cur.execute('UPDATE indexindex SET url = ? '
                        'WHERE namespace = ? and name = ?',
                        (url, name[0], name[1]))
    print('Total {}'.format(cur.execute('SELECT count(*) FROM indexindex')
                            .fetchone()[0]))


def links_to_crawl(crawl_stack):
    while crawl_stack:
        link = crawl_stack.pop()
        if len(link) == 3:
            yield link + (None,)
        else:
            yield link


def crawl_links(crawl_stack, conn):
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS relations
        (
        origin_namespace text, origin text,
        destination_namespace text, destination text,
        constraint pk_relations primary key(origin_namespace, origin,
        destination_namespace, destination)
        )
        ''')
    start_time = datetime.now()
    start_indexindex_count = int(
        c.execute('SELECT count(*) FROM indexindex')
        .fetchone()[0])
    start_relations_count = int(
        c.execute('SELECT count(*) FROM relations')
        .fetchone()[0])
    round_count = 0
    for namespace, name, url, referer in links_to_crawl(crawl_stack):
        current_time = datetime.now()
        tree = parse(url)
        if namespace is None:
            try:
                namespace = tree.xpath('//div[@class="pagetitle"]')[0] \
                    .text.strip()[:-1]
            except AttributeError:
                print('Error: There is no pagetitle on this page.')
                continue
            if namespace == '':
                namespace = 'Main'
        print("Fetching: {}/{} @ {}"
              .format(namespace, name, url))
        if c.execute('SELECT count(*) FROM indexindex '
                     'WHERE namespace = ? and name = ?',
                     (namespace, name)).fetchone()[0] != 0:
            last_crawled = c.execute('SELECT last_crawled FROM indexindex '
                                     'WHERE namespace = ? and name = ?',
                                     (namespace, name)).fetchone()
            if last_crawled is not None:
                if last_crawled[0] is not None:
                    if (current_time - last_crawled[0]).days < 1:
                        print("Skipping: {}/{} @ {} due to recent crawl"
                              .format(namespace, name, url))
                        continue
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
                next_crawl = (None, destination_name, destination_url,
                              (namespace, name))
                if next_crawl not in crawl_stack:
                    crawl_stack.append(next_crawl)
            except AttributeError:
                pass
        if referer is not None:
            try:
                c.execute('INSERT INTO relations VALUES (?, ?, ?, ?)',
                          (referer[0], referer[1], namespace, name))
            except sqlite3.IntegrityError:
                pass
        print('Crawling {}/{} @ {} completed at {}'
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
            print('-> indexindex: {} ({}/h) relations: {} ({}/h) '
                  'elasped {}'
                  .format(indexindex_count,
                          int(indexindex_count / elasped_hours),
                          relations_count,
                          int(relations_count / elasped_hours),
                          elasped))


general_help_string = '''
Usage: python crawler.py <command> <arguments>

commands:

    init:
        Usage: python crawler.py init <db-file>

        Crawls indexindex of TVTropes.
        If an entry already exists, it is updated to new url.
        If the process is inturruped in the middle, nothing will be saved.

    relation:
        Usage: python crawler.py relation <db-file>

        Crawls each pages and saves it to a table, using items in
        indexindex table as seeds. New pages are saved to indexindex table,
        and relationship of pages are saved to relations table.
        If indexindex table is not found, an error will be raised.

If a db file is not already present with each commands, one will be
automatically created.
'''.strip()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'init':
            if len(sys.argv) != 3:
                print('Usage: python crawler.py init <db-file>',
                      file=sys.stderr)
                raise SystemExit(1)
            db_file = sys.argv[2]
            conn = sqlite3.connect(db_file,
                                   detect_types=sqlite3.PARSE_DECLTYPES)
            c = conn.cursor()
            save_links(list_pages(), c)
            conn.commit()
        elif sys.argv[1] == 'relation':
            if len(sys.argv) != 3:
                print('Usage: python crawler.py relation <db-file>',
                      file=sys.stderr)
                raise SystemExit(1)
            db_file = sys.argv[2]
            conn = sqlite3.connect(db_file,
                                   detect_types=sqlite3.PARSE_DECLTYPES)
            c = conn.cursor()
            if c.execute("SELECT name FROM sqlite_master "
                         "WHERE name='indexindex'").fetchone() is None:
                print('indexindex table is not present on provided db-file, '
                      'exiting.', file=sys.stderr)
                raise SystemExit(1)
            seed = c.execute('SELECT namespace, name, url FROM indexindex '
                             'ORDER BY namespace asc, name asc').fetchall()
            crawl_links(seed, conn)
            conn.commit()
        else:
            print(general_help_string, file=sys.stderr)
            raise SystemExit(1)
    else:
        print(general_help_string, file=sys.stderr)
        raise SystemExit(1)
