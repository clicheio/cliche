

def test_work_has_awards(fx_works, fx_awards):
    assert fx_works.cardcaptor_sakura.awards == {fx_awards.seiun_award}


def test_work_has_genres(fx_works, fx_genres):
    assert fx_works.cardcaptor_sakura.genres == {
        fx_genres.comic, fx_genres.romance
    }


def test_work_has_people(fx_works, fx_people):
    people = set()
    for asso in fx_works.cardcaptor_sakura.credits:
        people.add(asso.person)
        assert asso.work == fx_works.cardcaptor_sakura
        assert asso.role == 'Artist'
    assert people == {
        fx_people.clamp_member_1, fx_people.clamp_member_2,
        fx_people.clamp_member_3, fx_people.clamp_member_4
    }
