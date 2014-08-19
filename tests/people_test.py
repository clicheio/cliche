

def test_team_has_members(fx_people, fx_teams):
    assert fx_teams.clamp.members == {
        fx_people.clamp_member_1,
        fx_people.clamp_member_2,
        fx_people.clamp_member_3,
        fx_people.clamp_member_4
    }


def test_person_has_awards(fx_people, fx_awards):
    assert fx_people.peter_jackson.awards == {
        fx_awards.hugo_award,
        fx_awards.nebula_award
    }
