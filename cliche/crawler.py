import os
import sqlite3
import urllib.parse

from datetime import datetime

from lxml.html import parse


INDEX_INDEX = 'http://tvtropes.org/pmwiki/index_report.php'
WIKI_PAGE = 'http://tvtropes.org/pmwiki/pmwiki.php/'


def list_pages(namespace_url=None):
    tree = parse(namespace_url or INDEX_INDEX)

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
        CREATE TABLE indexindex
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
            pass


def links_to_crawl(crawl_queue):
    while crawl_queue:
        link = crawl_queue.pop()
        if len(link) == 3:
            yield link + (None,)
        else:
            yield link


def crawl_links(crawl_queue, conn):
    c = conn.cursor()
    c.execute('''
        CREATE TABLE relations
        (
        origin_namespace text, origin text,
        destination_namespace text, destination text,
        constraint pk_relations primary key(origin_namespace, origin,
        destination_namespace, destination)
        )
        ''')
    for namespace, name, url, referer in links_to_crawl(crawl_queue):
        conn.commit()
        tree = parse(url)
        is_update = False
        if namespace is not None:
            is_update = True
        namespace = tree.xpath('//div[@class="pagetitle"]')[0] \
            .text.strip()[:-1]
        if namespace == '':
            namespace = 'Main'
        last_crawled = c.execute('SELECT last_crawled FROM indexindex '
                                 'WHERE namespace = ? and name = ?',
                                 (namespace, name)).fetchone()
        if last_crawled is not None:
            if last_crawled[0] is not None:
                if (datetime.now() - last_crawled[0]).days <= 0:
                    continue
        print("Crawling: {}/{} @ {}".format(namespace, name, url))
        last_crawled = datetime.now()
        if is_update:
            c.execute('''
                UPDATE indexindex SET last_crawled = ?
                WHERE namespace = ? and name = ?
                ''', (last_crawled, namespace, name))
        else:
            try:
                c.execute('INSERT INTO indexindex VALUES (?, ?, ?, ?)',
                          (namespace, name, url, last_crawled))
            except sqlite3.IntegrityError:
                pass
        for a in tree.xpath('//a[@class="twikilink"]'):
            try:
                destination_name = a.text.strip()
                destination_url = urllib.parse.urljoin(
                    WIKI_PAGE, a.attrib['href']
                )
                next_crawl = (None, destination_name, destination_url,
                              (namespace, name))
                if next_crawl not in crawl_queue:
                    crawl_queue.append(next_crawl)
            except AttributeError:
                pass
        if referer is not None:
            try:
                c.execute('INSERT INTO relations VALUES (?, ?, ?, ?)',
                          (referer[0], referer[1], namespace, name))
            except sqlite3.IntegrityError:
                pass
        print('Crawled: {}/{} @ {}, {}'
              .format(namespace, name, url, last_crawled))


if __name__ == '__main__':
    db_file = 'test.tmp'
    if os.path.isfile(db_file):
        os.remove(db_file)
    conn = sqlite3.connect(db_file, detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    print('Crawling: indexindex')
    save_links(list_pages(), c)
    conn.commit()

    seed = c.execute('SELECT namespace, name, url FROM indexindex '
                     'ORDER BY namespace asc, name asc').fetchall()
    crawl_links(seed, conn)
    conn.commit()
