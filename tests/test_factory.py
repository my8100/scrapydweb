# coding: utf8
from scrapydweb import create_app


def test_config():
    assert not create_app().testing
    assert create_app({'TESTING': True}).testing


def test_group(client):
    response = client.get('/1/overview/')
    assert b'fakegroup' in response.data


def test_scrapyd_auth(client):
    response = client.get('/1/overview/')
    assert b'fakeusername:fakepassword' in response.data


def test_hello(client):
    response = client.get('/hello')
    assert response.data == b'Hello, World!'
