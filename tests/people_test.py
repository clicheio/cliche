

def test_team_has_members(fx_people, fx_teams):
    assert fx_teams.team.members == {
        fx_people.artist, fx_people.artist_2,
        fx_people.artist_3, fx_people.artist_4
    }
