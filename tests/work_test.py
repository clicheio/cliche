from cliche.work import Credit, Role


def test_genres_of_work(fx_works, fx_genres):
    assert fx_works.cardcaptor_sakura.genres == {
        fx_genres.comic, fx_genres.romance
    }


def test_what_belong_to_genre(fx_works, fx_genres):
    assert fx_genres.romance.works == {fx_works.cardcaptor_sakura}


def test_person_made_works(fx_people, fx_works):
    assert fx_people.clamp_member_1.credits == {
        fx_works.skura_member_asso_1
    }
    assert fx_works.skura_member_asso_1.work == \
        fx_works.cardcaptor_sakura
    assert fx_people.peter_jackson.credits == {
        fx_works.lor_film_asso_1
    }
    assert fx_works.lor_film_asso_1.work == \
        fx_works.lord_of_rings_film


def test_credits_of_work(fx_works, fx_people, fx_teams):
    people = set()
    for credit in fx_works.cardcaptor_sakura.credits:
        people.add(credit.person)
        assert credit.work == fx_works.cardcaptor_sakura
        assert credit.role == Role.artist
        assert credit.team == fx_teams.clamp
    assert people == {
        fx_people.clamp_member_1, fx_people.clamp_member_2,
        fx_people.clamp_member_3, fx_people.clamp_member_4
    }


def test_franchise_has_works(fx_works, fx_franchises):
    assert fx_franchises.lord_of_rings.works == {
        fx_works.lord_of_rings_film
    }
    assert fx_franchises.iron_man.works == {
        fx_works.avengers
    }


def test_work_belongs_to_franchise(fx_works, fx_franchises):
    assert fx_works.lord_of_rings_film.franchises == {
        fx_franchises.lord_of_rings
    }
    assert fx_works.avengers.franchises == {
        fx_franchises.iron_man,
        fx_franchises.captain_america,
        fx_franchises.hulk,
        fx_franchises.thor
    }


def test_franchise_belongs_to_world(fx_franchises, fx_worlds):
    assert fx_franchises.lord_of_rings.world == fx_worlds.middle_earth
    assert fx_franchises.iron_man.world == fx_worlds.marvel_universe


def test_work_has_title(fx_works):
    assert len(fx_works.cardcaptor_sakura.titles) == 1
    for title in fx_works.cardcaptor_sakura.titles:
        assert title.work_id == fx_works.cardcaptor_sakura.id
        assert title.title == 'Cardcaptor Sakura'
        assert title.reference_count == 0

    assert len(fx_works.lord_of_rings_film.titles) == 1
    for title in fx_works.lord_of_rings_film.titles:
        assert title.work_id == fx_works.lord_of_rings_film.id
        assert title.title == \
            'The Lord of the Rings: The Fellowship of the Ring'
        assert title.reference_count == 0


def test_credit_removed_with_work(fx_session, fx_works, fx_people):
    cardcaptor_id = fx_works.cardcaptor_sakura.id

    # before delete the work.
    num_credits = fx_session.query(Credit).\
        filter_by(work_id=cardcaptor_id).\
        count()
    assert num_credits == 4

    fx_session.delete(fx_works.cardcaptor_sakura)
    fx_session.flush()

    # after delete the work.
    num_credits = fx_session.query(Credit).\
        filter_by(work_id=cardcaptor_id).\
        count()
    assert num_credits == 0


def test_credit_removed_with_person(fx_session, fx_works, fx_people):
    member_1_id = fx_people.clamp_member_1.id

    # before delete the person.
    num_credits = fx_session.query(Credit).\
        filter_by(person_id=member_1_id).\
        count()
    assert num_credits == 1

    fx_session.delete(fx_people.clamp_member_1)
    fx_session.flush()

    # after delete the person.
    num_credits = fx_session.query(Credit).\
        filter_by(person_id=member_1_id).\
        count()
    assert num_credits == 0
