from cliche.work import AwardWinner, Credit, Role


def test_work_wins_awards(fx_works, fx_awards):
    assert fx_works.cardcaptor_sakura.awards == {fx_awards.seiun_award}


def test_award_was_given_to_works(fx_works, fx_awards):
    assert fx_awards.seiun_award.works == {fx_works.cardcaptor_sakura}


def test_genres_of_work(fx_works, fx_genres):
    assert fx_works.cardcaptor_sakura.genres == {
        fx_genres.comic, fx_genres.romance
    }


def test_what_belong_to_genre(fx_works, fx_genres):
    assert fx_genres.romance.works == {fx_works.cardcaptor_sakura}


def test_person_has_awards(fx_people, fx_awards):
    assert fx_people.peter_jackson.awards == {
        fx_awards.hugo_award,
        fx_awards.nebula_award
    }


def test_winners_of_award(fx_people, fx_awards):
    assert fx_awards.hugo_award.persons == {fx_people.peter_jackson}


def test_person_made_works(fx_people, fx_works):
    assert fx_people.clamp_member_1.credits == {
        fx_works.skura_member_asso_1
    }
    assert fx_works.skura_member_asso_1.work == \
        fx_works.cardcaptor_sakura


def test_work_has_people(fx_works, fx_people):
    people = set()
    for asso in fx_works.cardcaptor_sakura.credits:
        people.add(asso.person)
        assert asso.work == fx_works.cardcaptor_sakura
        assert asso.role == Role.artist
    assert people == {
        fx_people.clamp_member_1, fx_people.clamp_member_2,
        fx_people.clamp_member_3, fx_people.clamp_member_4
    }


def test_award_winner_removed_with_award(fx_session, fx_awards, fx_people):
    hugo_award_id = fx_awards.hugo_award.id

    # before delete the award.
    num_award_winners = fx_session.query(AwardWinner).\
        filter_by(award_id=hugo_award_id).\
        count()
    assert num_award_winners == 1

    fx_session.delete(fx_awards.hugo_award)
    fx_session.flush()

    # after delete the award.
    num_award_winners = fx_session.query(AwardWinner).\
        filter_by(award_id=hugo_award_id).\
        count()
    assert num_award_winners == 0


def test_award_winner_removed_with_person(fx_session, fx_awards, fx_people):
    peter_jackson_id = fx_people.peter_jackson.id

    # before delete the person.
    num_award_winners = fx_session.query(AwardWinner).\
        filter_by(person_id=peter_jackson_id).\
        count()
    assert num_award_winners == 2

    fx_session.delete(fx_people.peter_jackson)
    fx_session.flush()

    # after delete the person.
    num_award_winners = fx_session.query(AwardWinner).\
        filter_by(person_id=peter_jackson_id).\
        count()
    assert num_award_winners == 0


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
