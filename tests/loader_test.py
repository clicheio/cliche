from cliche.services.wikipedia import loader as dbpedia
from cliche.services.wikipedia.workauthor import WorkAuthor


def test_loader(fx_session, fx_celery_app):
    dbpedia.load_page(1)
    num = fx_session.query(WorkAuthor).count()
    assert num == 100
