

def test_team_has_members(fx_people, fx_teams):
    assert fx_teams.team.members == {
        fx_people.artist, fx_people.artist_2,
        fx_people.artist_3, fx_people.artist_4
    }


def test_person_has_awards(fx_people, fx_awards):
    assert fx_people.person.awards == {fx_awards.award_2}
