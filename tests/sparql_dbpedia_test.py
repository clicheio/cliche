
import pytest

from .load_dbpedia import load_dbpedia, save_db


@pytest.fixture
def fx_table():
    TABLE = {
        'TABLENAME': 'allworks',
        'PRIMARY': 'work',
        'FOREIGN': 'author',
        'LIMIT': 30000,
        'COUNT': 8
        }
    return TABLE


@pytest.fixture
def fx_cursor(fx_table):
    db_file = '{}.tmp'.format(fx_table['TABLENAME'])
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    return c


def test_load_dbpedia(fx_table, fx_cursor):
    for y in range(0, fx_table['COUNT']):
        res = load_dbpedia(fx_table['LIMIT'], y)
        save_db(res, fx_table)
        qry = 'SELECT COUNT({}) FROM {}'.format(
            fx_table['PRIMARY'], fx_table['TABLENAME'])
        assert fx_cursor.execute(qry).fetchone()[0] <= fx_table['LIMIT']*(y+1)
