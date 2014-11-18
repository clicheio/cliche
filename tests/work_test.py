from cliche.work import (CliTvCorres, CliWikiCorres, Credit, Franchise, Role,
                         Work, World)


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
        fx_works.iron_man_film, fx_works.avengers
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


def test_work_has_characters(fx_session, fx_works, fx_characters):
    assert fx_works.avengers.characters == {
        fx_characters.iron_man_character, fx_characters.hulk_character
    }
    assert fx_works.iron_man_film.characters == {
        fx_characters.iron_man_character
    }
    assert fx_works.lord_of_rings_film.characters == {
        fx_characters.frodo
    }


def test_character_is_in_works(fx_session, fx_works, fx_characters):
    assert fx_characters.iron_man_character.works == {
        fx_works.avengers, fx_works.iron_man_film
    }
    assert fx_characters.hulk_character.works == {
        fx_works.avengers
    }
    assert fx_characters.frodo.works == {
        fx_works.lord_of_rings_film
    }


def test_character_is_derived(fx_session, fx_characters):
    sanzo = fx_characters.sanzo
    xuanzang = fx_characters.xuanzang
    samjang = fx_characters.samjang
    assert sanzo.original_character == xuanzang
    assert samjang.original_character == xuanzang
    assert xuanzang.derived_characters == {sanzo, samjang}


def test_works_have_tropes(fx_tropes):
    assert fx_tropes.attack_on_titan.tropes == {
        fx_tropes.the_ace,
        fx_tropes.action_girl,
        fx_tropes.behemoth_battle
    }

    assert fx_tropes.dragon_ball_z.tropes == {
        fx_tropes.the_ace,
        fx_tropes.ass_kicking_pose,
        fx_tropes.cute_is_evil
    }


def test_tropes_be_subordinate_to_works(fx_tropes):
    assert fx_tropes.the_ace.works == {
        fx_tropes.attack_on_titan,
        fx_tropes.dragon_ball_z
    }

    assert fx_tropes.action_girl.works == {fx_tropes.attack_on_titan}
    assert fx_tropes.behemoth_battle.works == {fx_tropes.attack_on_titan}

    assert fx_tropes.ass_kicking_pose.works == {fx_tropes.dragon_ball_z}
    assert fx_tropes.cute_is_evil.works == {fx_tropes.dragon_ball_z}


def test_correspondences(fx_corres):
    fx_corres.cli_work.tv_corres == {
        CliTvCorres(cli_work=fx_corres.cli_work,
                    tv_entity=fx_corres.tv_entity,
                    confidence=0.8),
    }
    fx_corres.cli_work.wiki_corres == {
        CliWikiCorres(cli_work=fx_corres.cli_work,
                      wiki_work=fx_corres.wiki_film,
                      confidence=0.9),
    }
    fx_corres.wiki_film.corres == {
        CliWikiCorres(cli_work=fx_corres.cli_work,
                      wiki_work=fx_corres.wiki_film,
                      confidence=0.9),
    }
    fx_corres.tv_entity.corres == {
        CliTvCorres(cli_work=fx_corres.cli_work,
                    tv_entity=fx_corres.tv_entity,
                    confidence=0.8),
    }


def test_discriminator():
    def assert_discriminator(cls):
        try:
            cls(type='changing_manually')
            assert False
        except AttributeError:
            pass

        ins = cls()
        try:
            ins.type = 'changing_manually'
            assert False
        except AttributeError:
            pass

    assert_discriminator(Franchise)
    assert_discriminator(Work)
    assert_discriminator(World)
