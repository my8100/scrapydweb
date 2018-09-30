# coding: utf8
from io import BytesIO

from utils import simple_ui


def test_logs_utf8(client):
    response = client.get('/1/logs/utf8/fakeproject/fakespider/fakejob/')
    assert b"No Such Resource" in response.data and not simple_ui(response.data)


def test_logs_stats(client):
    response = client.get('/1/logs/stats/fakeproject/fakespider/fakejob/')
    assert b"No Such Resource" in response.data and not simple_ui(response.data)


def test_logs_source_demo_txt(client):
    response = client.get('/logs/source/demo.txt')
    assert b"scrapy.utils.log" in response.data


def test_logs_uploaded_demo_txt(client):
    response = client.get('/1/logs/uploaded/demo.txt')
    assert b"Statistics" in response.data and not simple_ui(response.data)


# Location: http://127.0.0.1:5000/logs/uploaded/ttt.txt
def test_logs_upload(client):
    data = {
        'file': (BytesIO(b'my file contents'), "fake.log")
    }
    response = client.post('/1/logs/upload/', content_type='multipart/form-data', data=data)
    assert '/logs/uploaded/' in response.headers['Location']
