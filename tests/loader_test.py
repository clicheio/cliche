# import requests
# from sure import expect
# import httpretty


# @httpretty.activate
# def test_loader():
#     httpretty.enable()
#     httpretty.register_uri(httpretty.GET, 'http://dbpedia.org/sparql/',
#                            body='[{"title": "Test Deal"}]',
#                            content_type='application/json')
#     response = resquests.get('http://dbpedia.org/sparql')
#     expect(response.json()).to.equal([{"title": "test Deal"}])
#     httpretty.disable()
#     httpretty.reset()
