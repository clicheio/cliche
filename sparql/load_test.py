import sqlite3
import urllib.parse

from SPARQLWrapper import SPARQLWrapper, JSON
import pytest

from .load_dbpedia import load_dbpedia


@pytest.fixture
def fx_table():
    TABLE = {
        'TABLENAME': 'allworks3',
        'PRIMARY': 'work',
        'FOREIGN': 'author',
        'LIMIT': 40000,
        'COUNT': 7
        }
    return TABLE


@pytest.fixture
def fx_cursor(fx_table):
    db_file = '{}.tmp'.format(fx_table['TABLENAME'])
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE {} (
        {} text PRIMARY KEY,
        {FOREIGN} text,
        FOREIGN KEY({FOREIGN}) REFERENCES artists(artist)
    )
    '''.format(fx_table['TABLENAME'], fx_table['PRIMARY'],
               FOREIGN=fx_table['FOREIGN']))
    return c


def test_load_dbpedia(fx_table, fx_cursor):
    for y in range(0, fx_table['COUNT']):
        res = load_dbpedia(fx_table['LIMIT'], y)
        assert fx_cursor.execute(
            'SELECT COUNT({}) FROM {}'
            .format(fx_table['PRIMARY'], fx_table['TABLENAME']))
        .fetchone()[0] == x[3]*x[4]


def test_save_db(fx_table, fx_cursor):
    # import json
    # json_data = open('/Users/miaekim/Downloads/sparql-3')
    # data = json.load(json_data)
    assert fx_cursor.execute(
        'SELECT COUNT({}) FROM {}'
        .format(fx_table['PRIMARY'], fx_table['TABLENAME']))
    .fetchone()[0] == 231512
