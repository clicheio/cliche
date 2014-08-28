from cliche.people import TeamMembership


def test_team_has_members(fx_people, fx_teams):
    assert fx_teams.clamp.members == {
        fx_people.clamp_member_1,
        fx_people.clamp_member_2,
        fx_people.clamp_member_3,
        fx_people.clamp_member_4
    }


def test_person_has_teams(fx_people, fx_teams):
    assert fx_people.clamp_member_1.teams == {fx_teams.clamp}


def test_membership_removed_with_team(fx_session, fx_people, fx_teams):
    clamp_id = fx_people.clamp_member_1.id

    # before delete the team.
    num_memberships = fx_session.query(TeamMembership).\
        filter_by(team_id=clamp_id).\
        count()
    assert num_memberships == 4

    fx_session.delete(fx_teams.clamp)
    fx_session.flush()

    # after delete the team.
    num_memberships = fx_session.query(TeamMembership).\
        filter_by(team_id=clamp_id).\
        count()
    assert num_memberships == 0


def test_membership_removed_with_person(fx_session, fx_people, fx_teams):
    member_1_id = fx_people.clamp_member_1.id

    # before delete the person.
    num_memberships = fx_session.query(TeamMembership).\
        filter_by(member_id=member_1_id).\
        count()
    assert num_memberships == 1

    fx_session.delete(fx_people.clamp_member_1)
    fx_session.flush()

    # after delete the person.
    num_memberships = fx_session.query(TeamMembership).\
        filter_by(member_id=member_1_id).\
        count()
    assert num_memberships == 0
