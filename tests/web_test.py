from .web_utils import assert_contain_text


def test_index(fx_flask_client):
    rv = fx_flask_client.get('/')
    assert_contain_text('Cliche.io', 'h1', rv.data)
