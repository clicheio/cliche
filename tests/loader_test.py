from cliche.services.wikipedia import loader as dbpedia
from cliche.services.wikipedia.WorkAuthor import WorkAuthor


def test_loader(fx_session):
    dbpedia.load_page(1)
    num = fx_session.query(WorkAuthor).count()
    assert num == 100
