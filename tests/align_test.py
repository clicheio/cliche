def test_externel_ids_of_work(fx_external_ids):
    assert fx_external_ids.jane_eyre_ex
    assert fx_external_ids.jane_eyre_ex.wikipedia_id == \
        'http://dbpedia.org/resource/Jane_Eyre'
