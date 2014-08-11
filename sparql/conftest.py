import sqlite3
import urllib.parse
import time

from SPARQLWrapper import SPARQLWrapper, JSON
import pytest

from .load_dbpedia import load_dbpedia


@pytest.fixture
def __init__(fx_table):
    TABLE = fx_table
    db_file = '{}.tmp'.format(TABLE['TABLENAME'])
    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    # DROP TABLE IF EXISTS Testing;
    c.execute('''
        CREATE TABLE {} (
            {} text PRIMARY KEY,
            {FOREIGN} text,
            FOREIGN KEY({FOREIGN}) REFERENCES artists(artist)
        )
    '''.format(TABLE['TABLENAME'], TABLE['PRIMARY'], FOREIGN=TABLE['FOREIGN']))

