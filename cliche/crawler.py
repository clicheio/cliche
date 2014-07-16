import os
import sqlite3
import urllib.parse

from lxml.html import parse


INDEX_INDEX = 'http://tvtropes.org/pmwiki/index_report.php'


def list_pages(namespace_url=None):
    tree = parse(namespace_url or INDEX_INDEX)

    links = {
        a.text.strip(): a.attrib['href']
        for a in tree.xpath('//a[@class="twikilink"]')
    }

    if not namespace_url:
        links = {'Main/' + key: value for key, value in links.items()}
        namespaces = tree.xpath(
            '//a[starts-with(@href, "index_report.php?groupname=")]'
        )
        namespaces = {
            a.text.strip(): urllib.parse.urljoin(
                INDEX_INDEX, a.attrib['href']
            )
            for a in namespaces
        }

        for namespace, url in namespaces.items():
            links.update({
                '{}/{}'.format(namespace, key): value
                for key, value in list_pages(url).items()
            })

    return links


if __name__ == '__main__':
    db_file = 'test.tmp'
    links = list_pages()
    if os.path.isfile(db_file):
        os.remove(db_file)
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute('CREATE TABLE indexindex (name text, url text)')
    for name, url in links.items():
        c.execute('INSERT INTO indexindex VALUES ("{}", "{}")'
                  .format(name, url))
    for row in c.execute('SELECT * FROM indexindex ORDER BY name'):
        print(row)
