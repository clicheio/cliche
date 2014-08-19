

def test_work_has_awards(fx_works, fx_awards):
    assert fx_works.cardcaptor_sakura.awards == {fx_awards.seiun_award}


def test_work_has_genres(fx_works, fx_genres):
    assert fx_works.cardcaptor_sakura.genres == {
        fx_genres.comic, fx_genres.romance
    }
