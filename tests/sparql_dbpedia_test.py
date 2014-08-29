import logging
from urllib.error import HTTPError, URLError

from sparql import load_dbpedia as dbpedia


def test_load_dbpedia_is_save_db(
        fx_sparql_dbpedia_table,
        fx_sparql_dbpedia_cursor):
    """ Test: Do sparql.load_dbpedia modules's methods
                really save data into db? """
    qry = 'SELECT COUNT({}) FROM {}'.format(
        fx_sparql_dbpedia_table['PRIMARY'],
        fx_sparql_dbpedia_table['TABLENAME']
    )
    count = 0
    for y in range(0, fx_sparql_dbpedia_table['COUNT']):
        try:
            res = dbpedia.load_dbpedia(fx_sparql_dbpedia_table['LIMIT'], y)
        except HTTPError as e:
            logging.exception(
                'Connected to dbpedia.org but got status code %d: %s.',
                e.code, e.msg)
            return
        except URLError as e:
            logging.exception(
                'Failed to connect to dbpedia.org: %s.', e.msg)
            return

        dbpedia.save_db(res, fx_sparql_dbpedia_table)

        temp = fx_sparql_dbpedia_cursor.execute(qry)
        count_current_rows = temp.fetchone()[0]
        assert count <= count_current_rows
        assert count_current_rows > 0
        count = count_current_rows
