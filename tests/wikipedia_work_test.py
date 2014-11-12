from cliche.services.wikipedia.work import Entity, Artist, Work, Film, Book


def test_properties():
    properties = {
        'dbpedia-owl:wikiPageRevisionID',
        'rdfs:label',
        'dbpprop:country',
    }
    assert Entity.PROPERTIES == properties


def test_work_properties():
    work_properties = {
        'dbpedia-owl:wikiPageRevisionID',
        'rdfs:label',
        'dbpprop:country',
        'dbpedia-owl:writer',
        'dbpedia-owl:author',
        'dbpedia-owl:mainCharacter',
        'dbpedia-owl:previousWork',
    }
    assert Work.PROPERTIES == work_properties


def test_artist_properties():
    artist_properties = {
        'dbpedia-owl:wikiPageRevisionID',
        'rdfs:label',
        'dbpprop:country',
        'dbpedia-owl:notableWork',
    }
    assert Artist.PROPERTIES == artist_properties


def test_film_properties():
    film_properties = {
        'dbpedia-owl:wikiPageRevisionID',
        'rdfs:label',
        'dbpprop:country',
        'dbpedia-owl:writer',
        'dbpedia-owl:author',
        'dbpedia-owl:mainCharacter',
        'dbpedia-owl:previousWork',
        'dbpedia-owl:director',
    }
    assert Film.PROPERTIES == film_properties


def test_book_properties():
    book_properties = {
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
    }
    assert Book.PROPERTIES == book_properties
