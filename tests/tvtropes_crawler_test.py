import requests

from cliche.services.tvtropes.crawler import fetch_link


def test_fetch_link(monkeypatch, fx_session, fx_celery_app):

    url = 'http://tvtropes.org/pmwiki/pmwiki.php/Main/GodJob'
    text = '<div class="pagetitle"><div class="article_title"><h1>' \
           '<span>God Job</span></h1></div></div>'

    def mockreturn(path):
        req = requests.Request()
        req.url = url
        req.text = text
        return req

    monkeypatch.setattr(requests, "get", mockreturn)

    result = fetch_link(url, fx_session)
    assert result[-3:] == ('Main', 'God Job', url)

