

def test_work_has_awards(fx_works, fx_awards):
    assert fx_works.work.awards == {
        fx_awards.award, fx_awards.award_2
    }


def test_work_has_genres(fx_works, fx_genres):
    assert fx_works.work.genres == {
        fx_genres.genre, fx_genres.genre_2
    }


def test_work_has_team(fx_works, fx_teams):
    assert fx_works.work.team == fx_teams.team
