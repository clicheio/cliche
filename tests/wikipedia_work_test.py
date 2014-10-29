from cliche.services.wikipedia.work import Entity, Artist, Work, Film, Book


def test_get_entities():
    entities = [
        'dbpedia-owl:wikiPageRevisionID',
        'rdfs:label',
        'dbpprop:country',
    ]
    assert Entity.get_entities() == entities


def test_get_work_entities():
    work_entities = [
        'dbpedia-owl:wikiPageRevisionID',
        'rdfs:label',
        'dbpprop:country',
        'dbpedia-owl:writer',
        'dbpedia-owl:author',
        'dbpedia-owl:mainCharacter',
        'dbpedia-owl:previousWork',
    ]
    assert Work.get_entities() == work_entities


def test_get_artist_entities():
    artist_entities = [
        'dbpedia-owl:wikiPageRevisionID',
        'rdfs:label',
        'dbpprop:country',
        'dbpedia-owl:notableWork',
    ]
    assert Artist.get_entities() == artist_entities


def test_get_film_entities():
    film_entities = [
        'dbpedia-owl:wikiPageRevisionID',
        'rdfs:label',
        'dbpprop:country',
        'dbpedia-owl:writer',
        'dbpedia-owl:author',
        'dbpedia-owl:mainCharacter',
        'dbpedia-owl:previousWork',
        'dbpedia-owl:director',
    ]
    assert Film.get_entities() == film_entities


def test_get_book_entities():
    book_entities = [
        'dbpedia-owl:wikiPageRevisionID',
        'rdfs:label',
        'dbpprop:country',
        'dbpedia-owl:writer',
        'dbpedia-owl:author',
        'dbpedia-owl:mainCharacter',
        'dbpedia-owl:previousWork',
        'dbpedia-owl:illustrator',
        'dbpedia-owl:isbn',
        'dbpedia-owl:numberOfPages',
    ]
    assert Book.get_entities() == book_entities
