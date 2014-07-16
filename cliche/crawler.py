import os
import sqlite3
import urllib.parse

from lxml.html import parse


INDEX_INDEX = 'http://tvtropes.org/pmwiki/index_report.php'


def list_pages(namespace_url=None):
    tree = parse(namespace_url or INDEX_INDEX)

    for a in tree.xpath('//a[@class="twikilink"]'):
        name = a.text.strip()
        if namespace_url:
            yield (name,), a.attrib['href']
        else:
            yield ('Main', name), a.attrib['href']

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
        (namespace text, name text, url text)
    ''')
    for name, url in links:
        cur.execute('INSERT INTO indexindex VALUES (?, ?, ?)',
                    (name[0], name[1], url))


if __name__ == '__main__':
    db_file = 'test.tmp'
    if os.path.isfile(db_file):
        os.remove(db_file)
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    save_links(list_pages(), c)
    conn.commit()
    for row in c.execute('SELECT * FROM indexindex ORDER BY name'):
        print(row)
